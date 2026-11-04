import json
import re
from dataclasses import asdict

from notes.service import NotesService


def response(status: int, data=None) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": "" if data is None else json.dumps(data),
    }


def handle_request(
    method: str,
    path: str,
    body: str | None,
    service: NotesService,
    query: dict | None = None,
) -> dict:
    if path == "/notes":
        if method == "POST":
            try:
                data = json.loads(body if body is not None else "")

                if not isinstance(data, dict):
                    return response(400, {"error": "Serve un oggetto JSON"})

                note = service.create(
                    data.get("title"),
                    data.get("content", ""),
                )
            except (ValueError, TypeError) as error:
                return response(400, {"error": str(error)})

            return response(201, asdict(note))

        if method == "GET":
            query = query or {}
            raw_limit = query.get("limit", "20")
            cursor = query.get("cursor")

            if (
                not isinstance(raw_limit, str)
                or not re.fullmatch(r"[0-9]{1,3}", raw_limit)
            ):
                return response(400, {"error": "Limite non valido"})

            limit = int(raw_limit)

            if not 1 <= limit <= 100:
                return response(
                    400, {"error": "Il limite deve essere tra 1 e 100"}
                )

            if "cursor" in query and cursor is None:
                return response(400, {"error": "Cursore non valido"})

            try:
                page = service.list_page(limit=limit, cursor=cursor)
            except ValueError as error:
                return response(400, {"error": str(error)})

            data = {"notes": [asdict(note) for note in page.notes]}
            if page.next_cursor is not None:
                data["next_cursor"] = page.next_cursor

            return response(200, data)

        return response(405, {"error": "Metodo non consentito"})

    if path.startswith("/notes/"):
        note_id = path[len("/notes/"):]

        if not note_id or "/" in note_id:
            return response(404, {"error": "Percorso inesistente"})

        if method == "GET":
            note = service.get(note_id)

            if note is None:
                return response(404, {"error": "Nota inesistente"})

            return response(200, asdict(note))

        if method == "DELETE":
            if not service.delete(note_id):
                return response(404, {"error": "Nota inesistente"})

            return response(204)

        return response(405, {"error": "Metodo non consentito"})

    return response(404, {"error": "Percorso inesistente"})
