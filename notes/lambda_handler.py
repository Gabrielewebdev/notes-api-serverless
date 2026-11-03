import base64
import binascii
import os
from functools import lru_cache

import boto3

from notes.dynamodb_repository import DynamoDBNoteRepository
from notes.http import handle_request, response
from notes.service import NotesService


@lru_cache(maxsize=1)
def get_service() -> NotesService:
    table_name = os.environ["NOTES_TABLE_NAME"]
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return NotesService(DynamoDBNoteRepository(table))


def handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]
    body = event.get("body")

    if event.get("isBase64Encoded", False):
        try:
            body = base64.b64decode(
                body or "", validate=True
            ).decode("utf-8")
        except (ValueError, binascii.Error):
            return response(400, {"error": "Corpo della richiesta non valido"})

    return handle_request(method, path, body, get_service())
