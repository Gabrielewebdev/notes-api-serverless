from typing import Protocol

from notes.domain import Note, create_note


class NoteRepository(Protocol):
    def save(self, note: Note) -> None: ...
    def get(self, note_id: str) -> Note | None: ...
    def list(self) -> list[Note]: ...
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

    def list(self) -> list[Note]:
        return self.repository.list()

    def delete(self, note_id: str) -> bool:
        return self.repository.delete(note_id)


class InMemoryNoteRepository:
    def __init__(self):
        self.notes: dict[str, Note] = {}

    def save(self, note: Note) -> None:
        self.notes[note.id] = note

    def get(self, note_id: str) -> Note | None:
        return self.notes.get(note_id)

    def list(self) -> list[Note]:
        return sorted(
            self.notes.values(),
            key=lambda note: (note.created_at, note.id),
            reverse=True,
        )

    def delete(self, note_id: str) -> bool:
        return self.notes.pop(note_id, None) is not None
