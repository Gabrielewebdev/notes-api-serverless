import hashlib
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "lambda.zip"
FIXED_DATE = (2020, 1, 1, 0, 0, 0)


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    files = {}

    def add_file(name, content):
        parts = PurePosixPath(name).parts
        if (
            not parts
            or name.startswith("/")
            or ".." in parts
            or "\\" in name
        ):
            raise RuntimeError(f"Percorso non valido: {name}")

        if name in files:
            raise RuntimeError(f"File duplicato: {name}")

        files[name] = content

    with tempfile.TemporaryDirectory() as temporary:
        wheels = Path(temporary) / "wheels"

        subprocess.run(
            [
                sys.executable, "-m", "pip", "download",
                "--requirement", str(ROOT / "requirements.txt"),
                "--dest", str(wheels),
                "--platform", "manylinux2014_x86_64",
                "--python-version", "3.14",
                "--implementation", "cp",
                "--only-binary=:all:",
            ],
            check=True,
        )

        for wheel in sorted(wheels.glob("*.whl")):
            if not wheel.name.endswith("-none-any.whl"):
                raise RuntimeError(
                    f"Questa build supporta solo wheel Python puri: {wheel.name}"
                )

            with zipfile.ZipFile(wheel) as archive:
                for entry in archive.infolist():
                    if entry.is_dir():
                        continue

                    parts = PurePosixPath(entry.filename).parts

                    if parts[0].endswith(".data"):
                        if len(parts) > 1 and parts[1] == "scripts":
                            continue
                        raise RuntimeError(
                            f"Struttura wheel da gestire: {entry.filename}"
                        )

                    add_file(entry.filename, archive.read(entry))

        for path in sorted((ROOT / "notes").rglob("*")):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix in {".pyc", ".pyo"}
            ):
                continue

            add_file(
                path.relative_to(ROOT).as_posix(),
                path.read_bytes(),
            )

        temporary_zip = Path(temporary) / "lambda.zip"

        with zipfile.ZipFile(temporary_zip, "w") as archive:
            for name, content in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=FIXED_DATE)
                entry.create_system = 3
                entry.compress_type = zipfile.ZIP_STORED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, content)

        size = temporary_zip.stat().st_size
        if size >= 50 * 1024 * 1024:
            raise RuntimeError(
                "Pacchetto troppo grande per questa modalità di upload: "
                f"{size / 1024 / 1024:.2f} MiB"
            )

        OUTPUT.write_bytes(temporary_zip.read_bytes())

    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    print(f"Pacchetto creato: {OUTPUT}")
    print(f"Dimensione: {OUTPUT.stat().st_size / 1024 / 1024:.2f} MiB")
    print(f"SHA256: {digest}")


if __name__ == "__main__":
    main()
