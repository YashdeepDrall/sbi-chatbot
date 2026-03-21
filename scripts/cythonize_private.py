from __future__ import annotations

import argparse
import os
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup


ROOT_DIR = Path(__file__).resolve().parents[1]

PRIVATE_MODULES = [
    ("app.api.fraud", Path("app") / "api" / "fraud.py"),
    ("app.runtime.api_runtime", Path("app") / "runtime" / "api_runtime.py"),
    ("app.runtime.ui_runtime", Path("app") / "runtime" / "ui_runtime.py"),
    ("app.services.auth_service", Path("app") / "services" / "auth_service.py"),
    ("app.services.chat_service", Path("app") / "services" / "chat_service.py"),
    ("app.services.document_service", Path("app") / "services" / "document_service.py"),
    ("app.services.fraud_service", Path("app") / "services" / "fraud_service.py"),
    ("app.services.rag_service", Path("app") / "services" / "rag_service.py"),
    ("app.services.llm_service", Path("app") / "services" / "llm_service.py"),
    ("app.ml.embeddings", Path("app") / "ml" / "embeddings.py"),
    ("app.ml.vector_store", Path("app") / "ml" / "vector_store.py"),
]


def ensure_windows_build_tools_on_path() -> None:
    if os.name != "nt":
        return

    path_entries = []

    search_roots = [
        Path("C:/Program Files (x86)/Microsoft Visual Studio"),
        Path("C:/Program Files/Microsoft Visual Studio"),
    ]

    candidates = []
    for root in search_roots:
        if not root.exists():
            continue
        candidates.extend(root.glob("*/BuildTools/VC/Tools/MSVC/*/bin/HostX86/x64"))
        candidates.extend(root.glob("*/BuildTools/VC/Tools/MSVC/*/bin/HostX64/x64"))

    if not candidates:
        selected = None
    else:
        selected = sorted(candidates, reverse=True)[0]
        path_entries.append(str(selected))

    sdk_root = Path("C:/Program Files (x86)/Windows Kits/10/bin")
    if sdk_root.exists():
        sdk_candidates = list(sdk_root.glob("*/x64"))
        if sdk_candidates:
            path_entries.append(str(sorted(sdk_candidates, reverse=True)[0]))

    if not path_entries:
        return

    current_path = os.environ.get("PATH", "")
    missing_entries = [entry for entry in path_entries if entry.lower() not in current_path.lower()]
    if missing_entries:
        os.environ["PATH"] = os.pathsep.join(missing_entries + [current_path])


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile private SBI modules with Cython.")
    parser.add_argument("--build-lib", required=True, help="Output directory for compiled modules.")
    parser.add_argument("--build-temp", required=True, help="Temporary build directory.")
    args = parser.parse_args()

    ensure_windows_build_tools_on_path()

    extensions = [
        Extension(
            name=module_name,
            sources=[str(source_path)],
            extra_link_args=["/MANIFEST:NO"] if os.name == "nt" else [],
        )
        for module_name, source_path in PRIVATE_MODULES
    ]

    setup(
        name="sbi-private-modules",
        ext_modules=cythonize(
            extensions,
            build_dir=args.build_temp,
            compiler_directives={
                "language_level": "3",
            },
        ),
        script_args=[
            "build_ext",
            "--build-lib",
            args.build_lib,
            "--build-temp",
            args.build_temp,
        ],
    )


if __name__ == "__main__":
    main()
