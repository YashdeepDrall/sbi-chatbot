import os

from fastapi import FastAPI

from app.api import fraud
from app.services.bootstrap_service import (
    ensure_sbi_bootstrap,
    get_bootstrap_status,
    initialize_sbi_runtime,
    start_sbi_runtime_in_background,
)


def build_application() -> FastAPI:
    app = FastAPI(title="SBI Fraud Investigation Assistant Chatbot API")

    @app.on_event("startup")
    def startup_event():
        print("Starting up system...")

        bootstrap_mode = os.getenv("BOOTSTRAP_MODE", "sync").strip().lower()
        ensure_sbi_bootstrap()

        if bootstrap_mode == "background":
            start_sbi_runtime_in_background()
            print("Runtime bootstrap started in background mode.")
        else:
            initialize_sbi_runtime()
            print("System ready. SBI vector index built and SBI PDFs indexed if any.")

    app.include_router(fraud.router)

    @app.get("/")
    def home():
        return {
            "message": "SBI Fraud Investigation Assistant running",
            "bootstrap": get_bootstrap_status(),
        }

    @app.get("/health")
    def health():
        status = get_bootstrap_status()
        state = "ready"
        if status.get("error"):
            state = "error"
        elif not status.get("ready"):
            state = "warming_up"

        return {"status": state, "bootstrap": status}

    return app


app = build_application()
