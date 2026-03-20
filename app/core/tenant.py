import re
from fastapi import Request

def extract_bank_from_user(user_id: str):

    bank = re.match(r"[a-zA-Z]+", user_id)

    if bank:
        return bank.group().lower()

    raise Exception("Invalid userId")