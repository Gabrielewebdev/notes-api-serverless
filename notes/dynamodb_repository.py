from dataclasses import asdict

from notes.domain import Note


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

    def list(self) -> list[Note]:
        notes = []
        options = {"ConsistentRead": True}

        while True:
            result = self.table.scan(**options)
            notes.extend(Note(**item) for item in result.get("Items", []))

            last_key = result.get("LastEvaluatedKey")
            if not last_key:
                break

            options["ExclusiveStartKey"] = last_key

        return sorted(
            notes,
            key=lambda note: (note.created_at, note.id),
            reverse=True,
        )

    def delete(self, note_id: str) -> bool:
        result = self.table.delete_item(
            Key={"id": note_id},
            ReturnValues="ALL_OLD",
        )
        return "Attributes" in result
