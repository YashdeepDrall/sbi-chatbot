from fastapi import FastAPI
from app.api import fraud
from app.ml.vector_store import rebuild_vector_index, load_documents_from_bank_folders

app = FastAPI(title="AI Multi Bank Chatbot")


@app.on_event("startup")
def startup_event():
    """
    Startup steps:
    1. Load all existing vectors from MongoDB into memory + FAISS
    2. Index only new PDFs that are not already in MongoDB
    """
    print("Starting up system...")

    # Step 1: Rebuild FAISS index from MongoDB
    rebuild_vector_index()

    # Step 2: Index new PDFs only (category-based splitting handled in vector_store.py)
    load_documents_from_bank_folders()

    print("System ready. Vector index built and new PDFs indexed if any.")


# Include routers
app.include_router(fraud.router)


@app.get("/")
def home():
    return {"message": "AI Multi Bank Chatbot Running"}