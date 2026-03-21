#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SBI_RUNTIME_VENV:-${BASE_DIR}/.runtime-venv}"

cd "${BASE_DIR}"
exec "${VENV_DIR}/bin/python" -m streamlit run ui_entry.py --server.address 0.0.0.0 --server.port "${SBI_UI_PORT:-8501}"
