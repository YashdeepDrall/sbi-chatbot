from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from pymongo import ASCENDING

from app.core.config import SBI_BANK_DIR, SBI_BANK_ID, SBI_BANK_NAME, SBI_SOP_FILE
from app.db.mongodb import (
    cases_collection,
    chat_logs_collection,
    documents_collection,
    users_collection,
)


def ensure_sbi_bootstrap() -> None:
    default_user_id = os.getenv("SBI_DEFAULT_USER_ID", "sbi001")
    default_password = os.getenv("SBI_DEFAULT_PASSWORD", "0000")

    users_collection.create_index([("userId", ASCENDING)], unique=True)
    users_collection.create_index([("bankId", ASCENDING)])
    documents_collection.create_index([("bankId", ASCENDING), ("fileName", ASCENDING)])
    documents_collection.create_index([("bankId", ASCENDING), ("sourceFile", ASCENDING)])
    cases_collection.create_index([("bankId", ASCENDING), ("fileName", ASCENDING)])
    chat_logs_collection.create_index([("userId", ASCENDING), ("sessionId", ASCENDING), ("timestamp", ASCENDING)])

    users_collection.delete_many({"bankId": {"$ne": SBI_BANK_ID}})
    documents_collection.delete_many({"bankId": {"$ne": SBI_BANK_ID}})
    cases_collection.delete_many({"bankId": {"$ne": SBI_BANK_ID}})
    chat_logs_collection.delete_many({"bankId": {"$ne": SBI_BANK_ID}})

    now = datetime.now(timezone.utc)

    users_collection.update_one(
        {"userId": default_user_id},
        {
            "$set": {
                "userId": default_user_id,
                "password": default_password,
                "bankId": SBI_BANK_ID,
                "bankName": SBI_BANK_NAME,
                "role": "investigator",
                "updatedAt": now,
            },
            "$setOnInsert": {
                "createdAt": now,
            },
        },
        upsert=True,
    )

    sbi_sop_path = Path(SBI_BANK_DIR) / SBI_SOP_FILE
    if sbi_sop_path.exists():
        documents_collection.update_one(
            {
                "bankId": SBI_BANK_ID,
                "fileName": SBI_SOP_FILE,
                "isPDF": True,
            },
            {
                "$set": {
                    "bankId": SBI_BANK_ID,
                    "documentType": "SOP",
                    "fileName": SBI_SOP_FILE,
                    "filePath": str(sbi_sop_path),
                    "isPDF": True,
                    "updatedAt": now,
                },
                "$setOnInsert": {
                    "createdAt": now,
                },
            },
            upsert=True,
        )
