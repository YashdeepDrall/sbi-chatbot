import os
import re
from pypdf import PdfReader

from app.db.mongodb import documents_collection, fs
from app.ml.embeddings import generate_embedding
from app.ml.vector_store import add_vector


BASE_FOLDER = "banks"


def extract_text_from_pdf(file_path):

    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


# Optional: Split SOP by fraud category blocks
def split_by_category(text):

    pattern = r'([A-Z]{1,3}-\d{2}[\s\S]*?)(?=[A-Z]{1,3}-\d{2}|$)'

    matches = re.findall(pattern, text)

    return [m.strip() for m in matches]


# Fallback chunking
def split_text(text, chunk_size=500):

    chunks = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)

    return chunks


# -----------------------------
# STORE ACTUAL PDF IN GRIDFS
# -----------------------------
def store_pdf_in_db(file_path, bank_id):

    file_name = os.path.basename(file_path)

    existing = documents_collection.find_one({
        "bankId": bank_id,
        "fileName": file_name
    })

    if existing and "fileId" in existing:
        return existing["fileId"]

    with open(file_path, "rb") as f:

        file_id = fs.put(
            f,
            filename=file_name,
            bankId=bank_id
        )

    documents_collection.update_one(
        {
            "bankId": bank_id,
            "fileName": file_name
        },
        {
            "$set": {
                "fileId": str(file_id),
                "filePath": file_path
            }
        },
        upsert=True
    )

    return str(file_id)


# -----------------------------
# PROCESS DOCUMENT
# -----------------------------
def process_document(file_path, bank_id):

    text = extract_text_from_pdf(file_path)

    chunks = split_text(text)

    file_name = os.path.basename(file_path)

    # Store actual PDF in MongoDB
    file_id = store_pdf_in_db(file_path, bank_id)

    for chunk in chunks:

        embedding = generate_embedding(chunk)

        add_vector(
            embedding,
            chunk,
            bank_id,
            file_name,
            file_id
        )


# -----------------------------
# LOAD ALL BANK DOCUMENTS
# -----------------------------
def load_bank_documents():

    for bank in os.listdir(BASE_FOLDER):

        bank_path = os.path.join(BASE_FOLDER, bank)

        if not os.path.isdir(bank_path):
            continue

        bank_id = bank.lower()

        for file in os.listdir(bank_path):

            if not file.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(bank_path, file)

            exists = documents_collection.find_one({
                "bankId": bank_id,
                "fileName": file
            })

            if not exists:

                documents_collection.insert_one({
                    "bankId": bank_id,
                    "documentType": "SOP",
                    "fileName": file,
                    "filePath": file_path
                })

            # Always process for embeddings
            process_document(file_path, bank_id)

    print("Bank documents loaded and indexed successfully")
