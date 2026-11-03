from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class Note:
    id: str
    title: str
    content: str
    created_at: str


def create_note(title: str, content: str = "") -> Note:
    if not isinstance(title, str):
        raise ValueError("Il titolo deve essere una stringa")

    title = title.strip()

    if not title:
        raise ValueError("Il titolo è obbligatorio")

    if len(title) > 200:
        raise ValueError("Il titolo non può superare 200 caratteri")

    if not isinstance(content, str):
        raise ValueError("Il contenuto deve essere una stringa")

    if len(content) > 10_000:
        raise ValueError("Il contenuto non può superare 10000 caratteri")

    return Note(
        id=str(uuid4()),
        title=title,
        content=content,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
