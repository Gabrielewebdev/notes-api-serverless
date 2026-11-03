from dataclasses import asdict
from unittest.mock import Mock

import pytest

from notes.domain import Note
from notes.dynamodb_repository import DynamoDBNoteRepository


@pytest.fixture
def table():
    return Mock()


@pytest.fixture
def repository(table):
    return DynamoDBNoteRepository(table)


@pytest.fixture
def note():
    return Note(
        id="note-1",
        title="Prima nota",
        content="Contenuto",
        created_at="2026-11-03T10:00:00+00:00",
    )


def test_save_sends_note_to_dynamodb(repository, table, note):
    repository.save(note)

    table.put_item.assert_called_once_with(Item=asdict(note))


def test_get_returns_existing_note(repository, table, note):
    table.get_item.return_value = {"Item": asdict(note)}

    assert repository.get(note.id) == note
    table.get_item.assert_called_once_with(
        Key={"id": note.id},
        ConsistentRead=True,
    )


def test_get_missing_note_returns_none(repository, table):
    table.get_item.return_value = {}

    assert repository.get("inesistente") is None


def test_list_empty_table(repository, table):
    table.scan.return_value = {"Items": []}

    assert repository.list() == []


def test_list_reads_all_pages_and_sorts(repository, table, note):
    newer = Note(
        id="note-2",
        title="Seconda nota",
        content="",
        created_at="2026-11-03T11:00:00+00:00",
    )
    table.scan.side_effect = [
        {
            "Items": [asdict(note)],
            "LastEvaluatedKey": {"id": note.id},
        },
        {"Items": [asdict(newer)]},
    ]

    assert repository.list() == [newer, note]
    assert table.scan.call_count == 2
    table.scan.assert_called_with(
        ConsistentRead=True,
        ExclusiveStartKey={"id": note.id},
    )


@pytest.mark.parametrize("exists", [True, False])
def test_delete_reports_whether_note_existed(
    repository, table, note, exists
):
    table.delete_item.return_value = (
        {"Attributes": asdict(note)} if exists else {}
    )

    assert repository.delete(note.id) is exists
    table.delete_item.assert_called_once_with(
        Key={"id": note.id},
        ReturnValues="ALL_OLD",
    )
