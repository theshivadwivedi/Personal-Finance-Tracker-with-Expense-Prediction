import jwt
import datetime
from dotenv import load_dotenv
from bson import ObjectId
import os

load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGO = os.getenv("JWT_ALGORITHM", "HS256") or "HS256"

def create_token(user_id):
    user_id_str = str(user_id)
    payload = {
        "user_id": user_id_str,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload["user_id"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
