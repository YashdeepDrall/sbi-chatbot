import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import SBI_BANK_DIR, SBI_SOP_FILE  # noqa: E402
from app.services.bootstrap_service import ensure_sbi_bootstrap  # noqa: E402


def main():
    load_dotenv(ROOT_DIR / ".env")

    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "sbi_fraud_chatbot")
    default_user_id = os.getenv("SBI_DEFAULT_USER_ID", "sbi001")

    client = MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    db = client[db_name]
    ensure_sbi_bootstrap()

    sbi_sop_path = Path(SBI_BANK_DIR) / SBI_SOP_FILE

    print(f"SBI database is ready: {db_name}")
    print(f"Mongo URL: {mongo_url}")
    print(f"Seeded user: {default_user_id}")
    print(f"SBI SOP found: {'yes' if sbi_sop_path.exists() else 'no'}")


if __name__ == "__main__":
    main()
