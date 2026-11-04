import base64
import json
from unittest.mock import Mock

import pytest

from notes import lambda_handler
from notes.service import InMemoryNoteRepository, NotesService


def make_event(method, path, body=None, encoded=False):
    return {
        "version": "2.0",
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "body": body,
        "isBase64Encoded": encoded,
    }


@pytest.fixture
def service(monkeypatch):
    service = NotesService(InMemoryNoteRepository())
    monkeypatch.setattr(lambda_handler, "get_service", lambda: service)
    return service


def test_handler_creates_note(service):
    event = make_event(
        "POST",
        "/notes",
        json.dumps({"title": "Nota da Lambda"}),
    )

    result = lambda_handler.handler(event, None)

    assert result["statusCode"] == 201
    note = json.loads(result["body"])
    assert note["title"] == "Nota da Lambda"
    assert service.get(note["id"]) is not None


def test_handler_reads_note(service):
    note = service.create("Nota esistente")
    event = make_event("GET", f"/notes/{note.id}")

    result = lambda_handler.handler(event, None)

    assert result["statusCode"] == 200
    assert json.loads(result["body"])["id"] == note.id


def test_handler_decodes_base64_body(service):
    body = json.dumps({"title": "Nota codificata"}).encode("utf-8")
    encoded = base64.b64encode(body).decode("ascii")
    event = make_event("POST", "/notes", encoded, encoded=True)

    result = lambda_handler.handler(event, None)

    assert result["statusCode"] == 201
    assert json.loads(result["body"])["title"] == "Nota codificata"


@pytest.mark.parametrize("body", ["%%%", "/w=="])
def test_handler_rejects_invalid_encoding(service, body):
    event = make_event("POST", "/notes", body, encoded=True)

    result = lambda_handler.handler(event, None)

    assert result["statusCode"] == 400
    assert service.list() == []


def test_database_errors_propagate(monkeypatch):
    service = Mock()
    service.list_page.side_effect = RuntimeError("Database non disponibile")
    monkeypatch.setattr(lambda_handler, "get_service", lambda: service)
    event = make_event("GET", "/notes")

    with pytest.raises(RuntimeError, match="Database non disponibile"):
        lambda_handler.handler(event, None)
