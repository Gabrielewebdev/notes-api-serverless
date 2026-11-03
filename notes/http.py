import json
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
            return response(
                200,
                {"notes": [asdict(note) for note in service.list()]},
            )

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
