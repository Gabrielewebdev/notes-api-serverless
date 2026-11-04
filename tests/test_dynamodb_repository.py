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
    table.scan.assert_called_once_with(
        ConsistentRead=True,
        Limit=20,
    )


def test_list_returns_one_page_without_reading_the_next(
    repository, table, note
):
    table.scan.return_value = {
        "Items": [asdict(note)],
        "LastEvaluatedKey": {"id": note.id},
    }

    page = repository.list_page(limit=1)

    assert page.notes == [note]
    assert page.next_cursor == note.id
    table.scan.assert_called_once_with(
        ConsistentRead=True,
        Limit=1,
    )


def test_cursor_is_forwarded_and_final_page_has_no_cursor(
    repository, table, note
):
    table.scan.return_value = {"Items": [asdict(note)]}

    page = repository.list_page(limit=5, cursor="previous-note")

    assert page.notes == [note]
    assert page.next_cursor is None
    table.scan.assert_called_once_with(
        ConsistentRead=True,
        Limit=5,
        ExclusiveStartKey={"id": "previous-note"},
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
