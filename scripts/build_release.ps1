$ErrorActionPreference = "Stop"

& .\venv\Scripts\python.exe -m pip install -r requirements-build.txt
& .\venv\Scripts\python.exe scripts\build_release.py
