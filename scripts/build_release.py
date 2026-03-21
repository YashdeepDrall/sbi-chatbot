from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT_DIR / "build"
DIST_DIR = ROOT_DIR / "dist"
PRIVATE_BUILD_DIR = BUILD_DIR / "private_modules"
PRIVATE_TEMP_DIR = BUILD_DIR / "temp"
RELEASE_DIR = DIST_DIR / "sbi-release"
PRIVATE_SOURCE_RELATIVE_PATHS = {
    Path("streamlit_app.py"),
    Path("app/api/fraud.py"),
    Path("app/services/fraud_service.py"),
    Path("app/services/rag_service.py"),
    Path("app/services/llm_service.py"),
    Path("app/ml/vector_store.py"),
}


def clean_directories() -> None:
    for path in [PRIVATE_BUILD_DIR, PRIVATE_TEMP_DIR, RELEASE_DIR]:
        if path.exists():
            shutil.rmtree(path)

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_TEMP_DIR.mkdir(parents=True, exist_ok=True)


def compile_private_modules() -> None:
    command = [
        sys.executable,
        str(ROOT_DIR / "scripts" / "cythonize_private.py"),
        "--build-lib",
        str(PRIVATE_BUILD_DIR),
        "--build-temp",
        str(PRIVATE_TEMP_DIR),
    ]
    try:
        subprocess.run(command, cwd=ROOT_DIR, check=True)
    except subprocess.CalledProcessError as exc:
        raise SystemExit(
            "Private module compilation failed. Install the platform C compiler first "
            "(for Windows: Microsoft C++ Build Tools), or run the GitHub Actions pipeline "
            "on Linux to generate the release artifact."
        ) from exc


def copy_file(relative_path: str) -> None:
    source = ROOT_DIR / relative_path
    destination = RELEASE_DIR / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_directory(relative_path: str) -> None:
    source = ROOT_DIR / relative_path
    destination = RELEASE_DIR / relative_path
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def remove_private_sources() -> None:
    for relative_path in PRIVATE_SOURCE_RELATIVE_PATHS:
        candidate = RELEASE_DIR / relative_path
        if candidate.exists():
            candidate.unlink()


def copy_private_binaries() -> None:
    for compiled_file in PRIVATE_BUILD_DIR.rglob("*"):
        if compiled_file.is_dir():
            continue

        if compiled_file.suffix not in {".pyd", ".so", ".dll", ".dylib"}:
            continue

        relative_path = compiled_file.relative_to(PRIVATE_BUILD_DIR)
        destination = RELEASE_DIR / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(compiled_file, destination)


def build_release_folder() -> None:
    files_to_copy = [
        "requirements.txt",
        "requirements-build.txt",
        ".gitignore",
        "ui_entry.py",
        "app/__init__.py",
        "app/main.py",
        "app/api/__init__.py",
        "app/core/__init__.py",
        "app/core/config.py",
        "app/db/__init__.py",
        "app/db/mongodb.py",
        "app/ml/__init__.py",
        "app/ml/embeddings.py",
        "app/services/__init__.py",
        "app/services/auth_service.py",
        "app/services/chat_service.py",
        "app/services/document_service.py",
        "scripts/setup_sbi_db.py",
        "deploy/install_release.sh",
        "deploy/run_backend.sh",
        "deploy/run_streamlit.sh",
        "deploy/restart_app.sh",
        "deploy/runtime.env.example",
    ]
    directories_to_copy = [
        "banks/sbi",
    ]

    for relative_path in files_to_copy:
        copy_file(relative_path)

    for relative_path in directories_to_copy:
        copy_directory(relative_path)

    remove_private_sources()
    copy_private_binaries()


def create_archives() -> None:
    zip_path = DIST_DIR / "sbi-release.zip"
    tar_path = DIST_DIR / "sbi-release.tar.gz"

    if zip_path.exists():
        zip_path.unlink()
    if tar_path.exists():
        tar_path.unlink()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in RELEASE_DIR.rglob("*"):
            if file_path.is_file():
                zip_file.write(file_path, file_path.relative_to(DIST_DIR))

    with tarfile.open(tar_path, "w:gz") as tar_file:
        tar_file.add(RELEASE_DIR, arcname=RELEASE_DIR.name)


def main() -> None:
    clean_directories()
    compile_private_modules()
    build_release_folder()
    create_archives()

    print(f"Release folder created at: {RELEASE_DIR}")
    print(f"ZIP package created at: {DIST_DIR / 'sbi-release.zip'}")
    print(f"TAR package created at: {DIST_DIR / 'sbi-release.tar.gz'}")


if __name__ == "__main__":
    main()
