import faiss
import numpy as np
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import gridfs
import os
import re

# -----------------------------
# Embedding model
# -----------------------------
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# -----------------------------
# FAISS setup
# -----------------------------
vector_dimension = 384
index = faiss.IndexFlatL2(vector_dimension)

# -----------------------------
# MongoDB
# -----------------------------
client = MongoClient("mongodb://localhost:27017")
db = client["bank_chatbot"]
collection = db["documents"]

# GridFS for storing actual PDFs
fs = gridfs.GridFS(db)

# In-memory vector store
vector_store = []


# -----------------------------
# Generate embedding
# -----------------------------
def generate_embedding(text):
    return model.encode(text)


# -----------------------------
# Extract text from PDF
# -----------------------------
def extract_text_from_pdf(file_path):

    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    return text


# -----------------------------
# Split SOP by fraud category
# -----------------------------
def split_by_category(text):

    pattern = r'([A-Z]{1,3}-\d{2}[\s\S]*?)(?=[A-Z]{1,3}-\d{2}|$)'
    matches = re.findall(pattern, text)

    return [m.strip() for m in matches if m.strip()]


# -----------------------------
# Store PDF in GridFS
# -----------------------------
def store_pdf(file_path, bank_id):

    file_name = os.path.basename(file_path)

    # Check if already stored
    existing = collection.find_one({
        "bankId": bank_id,
        "fileName": file_name,
        "isPDF": True
    })

    if existing and "fileId" in existing:
        return existing["fileId"]

    with open(file_path, "rb") as f:

        file_id = fs.put(
            f,
            filename=file_name,
            bankId=bank_id
        )

    # Store reference in documents collection
    collection.insert_one({
        "bankId": bank_id,
        "fileName": file_name,
        "fileId": str(file_id),
        "isPDF": True
    })

    print(f"Stored PDF in MongoDB: {file_name}")

    return str(file_id)


# -----------------------------
# Add vector
# -----------------------------
def add_vector(embedding, text, bank_id, file_name, file_id):

    vector_np = np.array([embedding]).astype("float32")

    # Check duplicate chunk
    exists = collection.find_one({
        "bankId": bank_id,
        "fileName": file_name,
        "text": text[:120]
    })

    if exists:
        print(f"Skipping duplicate chunk for {file_name}")
        return

    index.add(vector_np)

    doc = {
        "bankId": bank_id,
        "fileName": file_name,
        "text": text,
        "embedding": embedding.tolist(),
        "fileId": file_id
    }

    vector_store.append(doc)

    collection.insert_one(doc)


# -----------------------------
# Rebuild FAISS index
# -----------------------------
def rebuild_vector_index():

    global vector_store

    print("Rebuilding FAISS index from MongoDB...")

    vector_store = []
    index.reset()

    docs = list(collection.find({"embedding": {"$exists": True}}))

    for doc in docs:

        embedding = np.array(doc["embedding"]).astype("float32")

        index.add(np.array([embedding]))

        vector_store.append(doc)

    print(f"Loaded {len(vector_store)} vectors from MongoDB")


# -----------------------------
# Load bank documents
# -----------------------------
def load_documents_from_bank_folders():

    base_path = "banks"

    if not os.path.exists(base_path):
        print("Banks folder not found")
        return

    for bank in os.listdir(base_path):

        bank_path = os.path.join(base_path, bank)

        if not os.path.isdir(bank_path):
            continue

        print(f"Checking documents for bank: {bank}")

        for file in os.listdir(bank_path):

            if not file.lower().endswith(".pdf"):
                continue

            file_path = os.path.join(bank_path, file)

            # Store PDF in GridFS
            file_id = store_pdf(file_path, bank)

            # Check if chunks already exist
            exists = collection.find_one({
                "bankId": bank,
                "fileName": {"$regex": f"^{file}_block"}
            })

            if exists:
                print(f"Skipping already indexed file: {file}")
                continue

            try:

                text = extract_text_from_pdf(file_path)

                if text.strip() == "":
                    print(f"Skipped empty PDF: {file}")
                    continue

                blocks = split_by_category(text)

                if not blocks:
                    blocks = [text]

                for i, block in enumerate(blocks):

                    embedding = generate_embedding(block)

                    block_file_name = f"{file}_block{i+1}"

                    add_vector(
                        embedding,
                        block,
                        bank,
                        block_file_name,
                        file_id
                    )

                print(f"Indexed {len(blocks)} blocks from {file}")

            except Exception as e:

                print(f"Error processing {file}: {e}")


# -----------------------------
# Search vector
# -----------------------------
def search_vector(query_embedding, bank_id, top_k=3):

    results = []

    for doc in vector_store:

        if doc["bankId"] != bank_id:
            continue

        similarity = np.dot(query_embedding, doc["embedding"]) / (
            np.linalg.norm(query_embedding) *
            np.linalg.norm(doc["embedding"])
        )

        results.append((similarity, doc))

    results.sort(reverse=True)

    return results[:top_k]
