from dataclasses import dataclass
import re
from typing import Protocol

from notes.domain import Note, create_note


@dataclass(frozen=True)
class NotePage:
    notes: list[Note]
    next_cursor: str | None = None


class NoteRepository(Protocol):
    def save(self, note: Note) -> None: ...
    def get(self, note_id: str) -> Note | None: ...
    def list_page(
        self, limit: int, cursor: str | None
    ) -> NotePage: ...
    def delete(self, note_id: str) -> bool: ...


class NotesService:
    def __init__(self, repository: NoteRepository):
        self.repository = repository

    def create(self, title: str, content: str = "") -> Note:
        note = create_note(title, content)
        self.repository.save(note)
        return note

    def get(self, note_id: str) -> Note | None:
        return self.repository.get(note_id)

    def list_page(
        self, limit: int = 20, cursor: str | None = None
    ) -> NotePage:
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("Il limite deve essere un intero tra 1 e 100")

        if cursor is not None:
            if (
                not isinstance(cursor, str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", cursor)
            ):
                raise ValueError("Cursore non valido")

        return self.repository.list_page(limit, cursor)

    def list(self) -> list[Note]:
        return self.list_page().notes

    def delete(self, note_id: str) -> bool:
        return self.repository.delete(note_id)


class InMemoryNoteRepository:
    def __init__(self):
        self.notes: dict[str, Note] = {}

    def save(self, note: Note) -> None:
        self.notes[note.id] = note

    def get(self, note_id: str) -> Note | None:
        return self.notes.get(note_id)

    def list_page(
        self, limit: int = 20, cursor: str | None = None
    ) -> NotePage:
        notes = sorted(self.notes.values(), key=lambda note: note.id)

        if cursor is not None:
            notes = [note for note in notes if note.id > cursor]

        selected = notes[:limit]
        next_cursor = (
            selected[-1].id if len(notes) > limit else None
        )
        return NotePage(selected, next_cursor)

    def list(self) -> list[Note]:
        return self.list_page().notes

    def delete(self, note_id: str) -> bool:
        return self.notes.pop(note_id, None) is not None
