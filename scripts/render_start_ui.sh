#!/usr/bin/env bash
set -euo pipefail

exec streamlit run streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT:-10000}" \
  --server.headless true
