from dataclasses import asdict

from notes.domain import Note
from notes.service import NotePage


class DynamoDBNoteRepository:
    def __init__(self, table):
        self.table = table

    def save(self, note: Note) -> None:
        self.table.put_item(Item=asdict(note))

    def get(self, note_id: str) -> Note | None:
        result = self.table.get_item(
            Key={"id": note_id},
            ConsistentRead=True,
        )
        item = result.get("Item")
        return Note(**item) if item is not None else None

    def list_page(
        self, limit: int = 20, cursor: str | None = None
    ) -> NotePage:
        options = {
            "ConsistentRead": True,
            "Limit": limit,
        }

        if cursor is not None:
            options["ExclusiveStartKey"] = {"id": cursor}

        result = self.table.scan(**options)
        notes = [Note(**item) for item in result.get("Items", [])]
        last_key = result.get("LastEvaluatedKey")

        return NotePage(
            notes=notes,
            next_cursor=last_key["id"] if last_key else None,
        )

    def list(self) -> list[Note]:
        return self.list_page().notes

    def delete(self, note_id: str) -> bool:
        result = self.table.delete_item(
            Key={"id": note_id},
            ReturnValues="ALL_OLD",
        )
        return "Attributes" in result
