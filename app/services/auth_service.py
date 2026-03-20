from app.db.mongodb import users_collection


def verify_user(user_id: str):
    user = users_collection.find_one({"userId": user_id})
    if not user:
        raise Exception(f"User {user_id} not found in database")
    return user["bankId"]


def verify_user_credentials(user_id: str, password: str):
    user = users_collection.find_one({"userId": user_id, "password": password})
    if not user:
        raise Exception("Invalid userId or password")
    return user["bankId"]
