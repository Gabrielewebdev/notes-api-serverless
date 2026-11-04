from unittest.mock import Mock

import pytest

from notes.service import InMemoryNoteRepository, NotesService


def test_pages_cover_all_notes_without_duplicates():
    service = NotesService(InMemoryNoteRepository())
    created = [service.create(f"Nota {number}") for number in range(5)]

    first = service.list_page(limit=2)
    assert len(first.notes) == 2
    assert first.next_cursor is not None

    second = service.list_page(limit=2, cursor=first.next_cursor)
    assert len(second.notes) == 2
    assert second.next_cursor is not None

    third = service.list_page(limit=2, cursor=second.next_cursor)
    assert len(third.notes) == 1
    assert third.next_cursor is None

    ids = [note.id for note in first.notes + second.notes + third.notes]
    assert len(ids) == len(set(ids)) == 5
    assert set(ids) == {note.id for note in created}


def test_default_list_is_limited_to_twenty_notes():
    service = NotesService(InMemoryNoteRepository())
    for number in range(25):
        service.create(f"Nota {number}")

    assert len(service.list()) == 20
    assert service.list_page().next_cursor is not None


@pytest.mark.parametrize("limit", [0, -1, 101, True, None, 1.5, "2"])
def test_invalid_limit_is_rejected_before_database_access(limit):
    repository = Mock()
    service = NotesService(repository)

    with pytest.raises(ValueError):
        service.list_page(limit=limit)

    repository.list_page.assert_not_called()


@pytest.mark.parametrize("cursor", ["", "a/b", " ", 123, "a" * 201])
def test_invalid_cursor_is_rejected_before_database_access(cursor):
    repository = Mock()
    service = NotesService(repository)

    with pytest.raises(ValueError):
        service.list_page(cursor=cursor)

    repository.list_page.assert_not_called()
