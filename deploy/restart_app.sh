#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "${BASE_DIR}/logs"

pkill -f "uvicorn app.main:app" || true
pkill -f "streamlit run ui_entry.py" || true

nohup bash "${BASE_DIR}/deploy/run_backend.sh" > "${BASE_DIR}/logs/backend.log" 2>&1 &
nohup bash "${BASE_DIR}/deploy/run_streamlit.sh" > "${BASE_DIR}/logs/streamlit.log" 2>&1 &

echo "SBI backend and Streamlit UI restarted."
