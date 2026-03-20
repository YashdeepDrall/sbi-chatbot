import os
from pymongo import MongoClient
from dotenv import load_dotenv
import gridfs

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

client = MongoClient(MONGO_URL)

db = client["bank_chatbot"]

users_collection = db["users"]
documents_collection = db["documents"]
cases_collection = db["historical_cases"]

# NEW COLLECTION
chat_logs_collection = db["chat_logs"]

# GRIDFS for storing actual PDF files
fs = gridfs.GridFS(db)