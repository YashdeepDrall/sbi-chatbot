# SBI Chatbot

This project is now scoped only for SBI fraud investigation workflows.

- Backend: FastAPI APIs for login, fraud analysis, SOP retrieval, and document download
- Frontend: Streamlit chat interface for SBI investigators
- Knowledge base: only `banks/sbi/SBI_SOP.pdf` is loaded and indexed
- Database: dedicated MongoDB database `sbi_fraud_chatbot`

Removed scope:

- HDFC-specific SOP support
- ICICI-specific SOP support
- Multi-bank UI and loader behavior

## SBI database setup

1. Update `.env` if you want a different Mongo URL, database name, or SBI login.
2. Run `.\venv\Scripts\python.exe scripts\setup_sbi_db.py`
3. Start the backend, then start the Streamlit app.

Default seeded SBI login:

- User ID: `sbi001`
- Password: `0000`

Change the password in `.env` before using this outside local development.

## Private build and release

Sensitive modules are compiled with Cython before deployment. The release package ships compiled binaries for:

- `streamlit_app.py`
- `app/api/fraud.py`
- `app/services/fraud_service.py`
- `app/services/rag_service.py`
- `app/services/llm_service.py`
- `app/ml/vector_store.py`

### Local build commands

Windows local build:

1. `.\venv\Scripts\python.exe -m pip install --upgrade pip`
2. `.\venv\Scripts\python.exe -m pip install -r requirements-build.txt`
3. `.\venv\Scripts\python.exe scripts\build_release.py`

Shortcut script:

- `powershell -ExecutionPolicy Bypass -File .\scripts\build_release.ps1`

Build output:

- `dist/sbi-release/`
- `dist/sbi-release.zip`
- `dist/sbi-release.tar.gz`

If Windows build stops with `Microsoft Visual C++ 14.0 or greater is required`, either install Microsoft C++ Build Tools on the build machine or use the GitHub Actions pipeline to build the Linux release artifact.

### Manual Linux server run commands

After copying `dist/sbi-release.tar.gz` to the target Linux server:

1. `mkdir -p /opt/sbi-chatbot/current`
2. `tar -xzf /tmp/sbi-release.tar.gz -C /opt/sbi-chatbot/current --strip-components=1`
3. `cd /opt/sbi-chatbot/current`
4. `bash deploy/install_release.sh`
5. `bash deploy/restart_app.sh`

### CI/CD workflow

GitHub Actions workflow file:

- `.github/workflows/build-and-deploy.yml`

Current placeholder cloud values inside the workflow:

- SSH host: `203.0.113.10`
- SSH user: `root`
- SSH port: `22`
- Deploy path: `/opt/sbi-chatbot`

Required GitHub secret:

- `CLOUD_SSH_PRIVATE_KEY`
