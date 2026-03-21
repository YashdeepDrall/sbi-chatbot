#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${SBI_RUNTIME_VENV:-${BASE_DIR}/.runtime-venv}"

mkdir -p "${BASE_DIR}/logs"

python3 -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${BASE_DIR}/requirements.txt"

chmod +x "${BASE_DIR}/deploy/run_backend.sh"
chmod +x "${BASE_DIR}/deploy/run_streamlit.sh"
chmod +x "${BASE_DIR}/deploy/restart_app.sh"

echo "Runtime environment ready at ${VENV_DIR}"
