#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install -r requirements-build.txt
python3 scripts/build_release.py
