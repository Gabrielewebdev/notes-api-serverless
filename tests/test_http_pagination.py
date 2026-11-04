import json
from unittest.mock import Mock

import pytest

from notes import lambda_handler
from notes.http import handle_request
from notes.service import InMemoryNoteRepository, NotesService


@pytest.fixture
def service():
    return NotesService(InMemoryNoteRepository())


def test_http_pagination_returns_all_notes_once(service):
    created = [service.create(f"Nota {number}") for number in range(5)]
    query = {"limit": "2"}
    seen = []

    for _ in range(5):
        result = handle_request(
            "GET", "/notes", None, service, query=query
        )
        assert result["statusCode"] == 200
        data = json.loads(result["body"])
        assert len(data["notes"]) <= 2
        seen.extend(note["id"] for note in data["notes"])

        cursor = data.get("next_cursor")
        if cursor is None:
            break
        query = {"limit": "2", "cursor": cursor}
    else:
        pytest.fail("La paginazione non termina")

    assert len(seen) == len(set(seen)) == 5
    assert set(seen) == {note.id for note in created}


@pytest.mark.parametrize(
    "query",
    [
        {"limit": "0"},
        {"limit": "101"},
        {"limit": "-1"},
        {"limit": "abc"},
        {"limit": ""},
        {"limit": "1.5"},
        {"limit": "1,2"},
        {"cursor": ""},
        {"cursor": "a/b"},
        {"cursor": None},
    ],
)
def test_invalid_query_is_rejected_before_database_access(query):
    repository = Mock()
    service = NotesService(repository)

    result = handle_request(
        "GET", "/notes", None, service, query=query
    )

    assert result["statusCode"] == 400
    repository.list_page.assert_not_called()


def test_lambda_forwards_query_parameters(monkeypatch, service):
    for number in range(3):
        service.create(f"Nota {number}")

    monkeypatch.setattr(lambda_handler, "get_service", lambda: service)
    event = {
        "version": "2.0",
        "requestContext": {"http": {"method": "GET"}},
        "rawPath": "/notes",
        "queryStringParameters": {"limit": "1"},
    }

    first = lambda_handler.handler(event, None)
    assert first["statusCode"] == 200
    first_data = json.loads(first["body"])
    assert len(first_data["notes"]) == 1
    assert "next_cursor" in first_data

    event["queryStringParameters"]["cursor"] = first_data["next_cursor"]
    second = lambda_handler.handler(event, None)
    assert second["statusCode"] == 200
    second_data = json.loads(second["body"])
    assert len(second_data["notes"]) == 1
    assert first_data["notes"][0]["id"] != second_data["notes"][0]["id"]
