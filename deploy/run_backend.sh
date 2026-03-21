#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SBI_RUNTIME_VENV:-${BASE_DIR}/.runtime-venv}"

cd "${BASE_DIR}"
exec "${VENV_DIR}/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port "${SBI_API_PORT:-8000}"
