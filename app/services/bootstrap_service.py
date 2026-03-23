from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock, Thread

from pymongo import ASCENDING

from app.core.config import SBI_BANK_DIR, SBI_BANK_ID, SBI_BANK_NAME, SBI_SOP_FILE
from app.db.mongodb import (
    cases_collection,
    chat_logs_collection,
    documents_collection,
    users_collection,
)
from app.ml.vector_store import load_sbi_documents, rebuild_vector_index


_bootstrap_lock = Lock()
_bootstrap_state = {
    "started": False,
    "ready": False,
    "error": "",
    "mode": "sync",
}


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


def initialize_sbi_runtime() -> None:
    with _bootstrap_lock:
        _bootstrap_state["started"] = True
        _bootstrap_state["ready"] = False
        _bootstrap_state["error"] = ""

    try:
        rebuild_vector_index()
        load_sbi_documents()
        rebuild_vector_index()
    except Exception as exc:
        with _bootstrap_lock:
            _bootstrap_state["error"] = str(exc)
        raise

    with _bootstrap_lock:
        _bootstrap_state["ready"] = True
        _bootstrap_state["error"] = ""


def _run_background_runtime_bootstrap() -> None:
    try:
        initialize_sbi_runtime()
    except Exception as exc:
        print(f"Background runtime bootstrap failed: {exc}")


def start_sbi_runtime_in_background() -> None:
    with _bootstrap_lock:
        if _bootstrap_state["started"] and not _bootstrap_state["error"]:
            return
        _bootstrap_state["started"] = True
        _bootstrap_state["ready"] = False
        _bootstrap_state["error"] = ""

    Thread(target=_run_background_runtime_bootstrap, daemon=True).start()


def get_bootstrap_status() -> dict:
    with _bootstrap_lock:
        return dict(_bootstrap_state)
