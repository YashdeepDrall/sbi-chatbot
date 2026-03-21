from __future__ import annotations

import argparse
from pathlib import Path

from Cython.Build import cythonize
from setuptools import Extension, setup


ROOT_DIR = Path(__file__).resolve().parents[1]

PRIVATE_MODULES = [
    ("app.api.fraud", ROOT_DIR / "app" / "api" / "fraud.py"),
    ("app.services.fraud_service", ROOT_DIR / "app" / "services" / "fraud_service.py"),
    ("app.services.rag_service", ROOT_DIR / "app" / "services" / "rag_service.py"),
    ("app.services.llm_service", ROOT_DIR / "app" / "services" / "llm_service.py"),
    ("app.ml.vector_store", ROOT_DIR / "app" / "ml" / "vector_store.py"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile private SBI modules with Cython.")
    parser.add_argument("--build-lib", required=True, help="Output directory for compiled modules.")
    parser.add_argument("--build-temp", required=True, help="Temporary build directory.")
    args = parser.parse_args()

    extensions = [
        Extension(
            name=module_name,
            sources=[str(source_path)],
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
