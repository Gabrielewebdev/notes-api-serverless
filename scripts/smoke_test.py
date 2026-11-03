import json
import subprocess
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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
            "--profile", "portfolio", "--format", "process",
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

    note_id = None
    try:
        created = call(
            "POST", "/notes", 201,
            {"title": "Test AWS", "content": "Verifica end-to-end"},
        )
        note_id = created["id"]
        path = f"/notes/{note_id}"

        retrieved = call("GET", path, 200)
        assert retrieved == created, "La nota letta non coincide"

        listed = call("GET", "/notes", 200)
        assert created in listed["notes"], "Nota assente dall'elenco"

        call("POST", "/notes", 400, {"title": ""})

        call("DELETE", path, 204)
        note_id = None

        call("GET", path, 404)
        print("TUTTE LE VERIFICHE SUPERATE")
    finally:
        if note_id is not None:
            call("DELETE", f"/notes/{note_id}", 204)


if __name__ == "__main__":
    main()
