from datetime import datetime
from uuid import UUID

import pytest

from notes.domain import create_note


def test_create_note():
    note = create_note("Prima nota", "Sto imparando Python")

    assert note.title == "Prima nota"
    assert note.content == "Sto imparando Python"
    assert str(UUID(note.id)) == note.id
    assert datetime.fromisoformat(note.created_at).utcoffset().total_seconds() == 0


def test_title_spaces_are_removed():
    note = create_note("  Prima nota  ")

    assert note.title == "Prima nota"
    assert note.content == ""


@pytest.mark.parametrize("title", ["", "   ", None, 123, "a" * 201])
def test_invalid_title_is_rejected(title):
    with pytest.raises(ValueError):
        create_note(title)


@pytest.mark.parametrize("content", [None, 123, "a" * 10_001])
def test_invalid_content_is_rejected(content):
    with pytest.raises(ValueError):
        create_note("Titolo valido", content)


def test_maximum_lengths_are_accepted():
    note = create_note("a" * 200, "b" * 10_000)

    assert len(note.title) == 200
    assert len(note.content) == 10_000


def test_each_note_has_a_different_id():
    first = create_note("Titolo")
    second = create_note("Titolo")

    assert first.id != second.id
