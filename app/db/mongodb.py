import os
import gridfs
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "sbi_fraud_chatbot")
MONGO_USERS_COLLECTION = os.getenv("MONGO_USERS_COLLECTION", "users")
MONGO_DOCUMENTS_COLLECTION = os.getenv("MONGO_DOCUMENTS_COLLECTION", "documents")
MONGO_CASES_COLLECTION = os.getenv("MONGO_CASES_COLLECTION", "historical_cases")
MONGO_CHAT_LOGS_COLLECTION = os.getenv("MONGO_CHAT_LOGS_COLLECTION", "chat_logs")

_client = None
_db = None
_fs = None


def get_client():
    global _client

    if _client is None:
        server_selection_timeout_ms = int(
            os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")
        )
        _client = MongoClient(
            MONGO_URL,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
        )

    return _client


def get_db():
    global _db

    if _db is None:
        _db = get_client()[MONGO_DB_NAME]

    return _db


def get_fs():
    global _fs

    if _fs is None:
        _fs = gridfs.GridFS(get_db())

    return _fs


class LazyCollectionProxy:
    def __init__(self, collection_name):
        self.collection_name = collection_name

    def _collection(self):
        return get_db()[self.collection_name]

    def __getattr__(self, item):
        return getattr(self._collection(), item)


class LazyGridFSProxy:
    def __getattr__(self, item):
        return getattr(get_fs(), item)


users_collection = LazyCollectionProxy(MONGO_USERS_COLLECTION)
documents_collection = LazyCollectionProxy(MONGO_DOCUMENTS_COLLECTION)
cases_collection = LazyCollectionProxy(MONGO_CASES_COLLECTION)
chat_logs_collection = LazyCollectionProxy(MONGO_CHAT_LOGS_COLLECTION)

fs = LazyGridFSProxy()
