import json

import pytest

from notes.http import handle_request
from notes.service import InMemoryNoteRepository, NotesService


@pytest.fixture
def service():
    return NotesService(InMemoryNoteRepository())


def test_create_read_list_delete_flow(service):
    created = handle_request(
        "POST",
        "/notes",
        json.dumps({"title": "Prima nota", "content": "Contenuto"}),
        service,
    )

    assert created["statusCode"] == 201
    note = json.loads(created["body"])
    assert note["title"] == "Prima nota"
    assert note["content"] == "Contenuto"

    path = f"/notes/{note['id']}"

    retrieved = handle_request("GET", path, None, service)
    assert retrieved["statusCode"] == 200
    assert json.loads(retrieved["body"]) == note

    listed = handle_request("GET", "/notes", None, service)
    assert listed["statusCode"] == 200
    assert json.loads(listed["body"]) == {"notes": [note]}

    deleted = handle_request("DELETE", path, None, service)
    assert deleted["statusCode"] == 204
    assert deleted["body"] == ""

    missing = handle_request("GET", path, None, service)
    assert missing["statusCode"] == 404

    listed = handle_request("GET", "/notes", None, service)
    assert json.loads(listed["body"]) == {"notes": []}


@pytest.mark.parametrize(
    "body",
    [
        None,
        "",
        "{",
        "null",
        "[]",
        '{"content": "Manca il titolo"}',
        '{"title": ""}',
        '{"title": 123}',
        '{"title": "Valido", "content": null}',
    ],
)
def test_invalid_request_returns_400(body, service):
    result = handle_request("POST", "/notes", body, service)

    assert result["statusCode"] == 400
    assert service.list() == []


@pytest.mark.parametrize("method", ["GET", "DELETE"])
def test_missing_note_returns_404(method, service):
    result = handle_request(
        method, "/notes/inesistente", None, service
    )

    assert result["statusCode"] == 404


def test_unknown_path_returns_404(service):
    result = handle_request("GET", "/altro", None, service)

    assert result["statusCode"] == 404


@pytest.mark.parametrize("path", ["/notes", "/notes/123"])
def test_unsupported_method_returns_405(path, service):
    result = handle_request("PATCH", path, None, service)

    assert result["statusCode"] == 405
