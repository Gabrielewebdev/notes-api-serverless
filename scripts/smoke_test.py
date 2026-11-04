import json
import subprocess
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials


def main():
    api_url = subprocess.check_output(
        ["terraform", "-chdir=infra", "output", "-raw", "api_url"],
        text=True,
    ).strip()

    exported = json.loads(subprocess.check_output(
        [
            "aws", "configure", "export-credentials",
            "--format", "process",
        ],
        text=True,
    ))

    credentials = Credentials(
        exported["AccessKeyId"],
        exported["SecretAccessKey"],
        exported.get("SessionToken"),
    )

    def call(method, path, expected, data=None):
        time.sleep(0.6)
        body = None if data is None else json.dumps(data).encode("utf-8")
        url = api_url + path

        signed = AWSRequest(
            method=method,
            url=url,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        SigV4Auth(credentials, "execute-api", "us-east-1").add_auth(signed)

        request = Request(
            url,
            data=body,
            headers=dict(signed.headers.items()),
            method=method,
        )

        try:
            with urlopen(request, timeout=30) as result:
                status = result.status
                text = result.read().decode("utf-8")
        except HTTPError as error:
            status = error.code
            text = error.read().decode("utf-8")

        print(f"{method} {path} -> {status}")
        if status != expected:
            raise RuntimeError(
                f"Atteso {expected}, ricevuto {status}: {text}"
            )

        return json.loads(text) if text else None

    created = []
    marker = str(uuid4())

    try:
        for number in range(3):
            note = call(
                "POST", "/notes", 201,
                {
                    "title": f"Smoke test {marker} - {number}",
                    "content": "Verifica end-to-end e paginazione",
                },
            )
            created.append(note)

        for note in created:
            retrieved = call("GET", f"/notes/{note['id']}", 200)
            assert retrieved == note, "La nota letta non coincide"

        expected_ids = {note["id"] for note in created}
        seen_ids = set()
        used_cursors = set()
        cursor = None
        pages = 0

        for _ in range(100):
            query = {"limit": "2"}
            if cursor is not None:
                query["cursor"] = cursor

            page = call("GET", "/notes?" + urlencode(query), 200)
            notes = page["notes"]

            assert len(notes) <= 2, "Limite della pagina non rispettato"

            for note in notes:
                assert note["id"] not in seen_ids, "Nota duplicata tra pagine"
                seen_ids.add(note["id"])

            pages += 1
            cursor = page.get("next_cursor")

            if cursor is None:
                break

            assert cursor not in used_cursors, "Cursore ripetuto"
            used_cursors.add(cursor)
        else:
            raise RuntimeError("Superato il limite di 100 pagine del test")

        assert expected_ids <= seen_ids, "Note di prova assenti dall'elenco"
        assert pages >= 2, "La verifica non ha attraversato più pagine"

        call("GET", "/notes?limit=0", 400)
        call("GET", "/notes?limit=101", 400)
        call("GET", "/notes?cursor=invalid%2Fcursor", 400)
        call("POST", "/notes", 400, {"title": ""})

    finally:
        cleanup_errors = []

        for note in created:
            try:
                path = f"/notes/{note['id']}"
                call("DELETE", path, 204)
                call("GET", path, 404)
            except Exception as error:
                cleanup_errors.append((note["id"], str(error)))

        if cleanup_errors:
            raise RuntimeError(
                f"Pulizia delle note di prova incompleta: {cleanup_errors}"
            )

    print("TUTTE LE VERIFICHE SUPERATE, INCLUSA LA PAGINAZIONE")


if __name__ == "__main__":
    main()
