from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "lambda.zip"


def main():
    OUTPUT.parent.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory() as temporary:
        package = Path(temporary) / "package"

        subprocess.run(
            [
                sys.executable, "-m", "pip", "install",
                "--requirement", str(ROOT / "requirements.txt"),
                "--target", str(package),
                "--platform", "manylinux2014_x86_64",
                "--python-version", "3.14",
                "--implementation", "cp",
                "--only-binary=:all:",
                "--no-compile",
            ],
            check=True,
        )

        shutil.copytree(
            ROOT / "notes",
            package / "notes",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

        with zipfile.ZipFile(OUTPUT, "w") as archive:
            for path in sorted(package.rglob("*")):
                if not path.is_file() or "__pycache__" in path.parts:
                    continue

                entry = zipfile.ZipInfo(
                    path.relative_to(package).as_posix(),
                    date_time=(2020, 1, 1, 0, 0, 0),
                )
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes())

    print(f"Pacchetto creato: {OUTPUT}")


if __name__ == "__main__":
    main()
