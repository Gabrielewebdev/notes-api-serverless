import pytest

from notes.service import InMemoryNoteRepository, NotesService


@pytest.fixture
def service():
    return NotesService(InMemoryNoteRepository())


def test_created_note_can_be_retrieved(service):
    note = service.create("Prima nota", "Contenuto")

    assert service.get(note.id) == note


def test_list_is_initially_empty(service):
    assert service.list() == []


def test_list_contains_all_created_notes(service):
    first = service.create("Prima")
    second = service.create("Seconda")

    notes = service.list()

    assert len(notes) == 2
    assert {note.id for note in notes} == {first.id, second.id}


def test_delete_removes_only_the_requested_note(service):
    first = service.create("Prima")
    second = service.create("Seconda")

    assert service.delete(first.id) is True
    assert service.get(first.id) is None
    assert service.get(second.id) == second
    assert service.list() == [second]


def test_get_missing_note_returns_none(service):
    assert service.get("inesistente") is None


def test_delete_missing_note_returns_false(service):
    assert service.delete("inesistente") is False


def test_invalid_note_is_not_saved(service):
    with pytest.raises(ValueError):
        service.create("")

    assert service.list() == []
