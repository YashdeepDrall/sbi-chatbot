from fastapi import FastAPI

from app.api import fraud
from app.ml.vector_store import rebuild_vector_index, load_sbi_documents
from app.services.bootstrap_service import ensure_sbi_bootstrap


def build_application() -> FastAPI:
    app = FastAPI(title="SBI Fraud Investigation Assistant Chatbot API")

    @app.on_event("startup")
    def startup_event():
        """
        Startup steps:
        1. Load existing SBI vectors from MongoDB into memory + FAISS
        2. Index only new SBI PDFs that are not already in MongoDB
        """
        print("Starting up system...")

        ensure_sbi_bootstrap()
        rebuild_vector_index()
        load_sbi_documents()
        print("System ready. SBI vector index built and SBI PDFs indexed if any.")

    app.include_router(fraud.router)

    @app.get("/")
    def home():
        return {"message": "SBI Fraud Investigation Assistant running"}

    return app


app = build_application()
