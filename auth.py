# auth.py
import os
import time
import jwt
from dotenv import load_dotenv

load_dotenv()

def _get_secret(name, default=None):
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default

JWT_SECRET = _get_secret("JWT_SECRET") or "CHANGE_ME"
JWT_ALG = _get_secret("JWT_ALGORITHM") or "HS256"
JWT_EXP_SECONDS = int(os.getenv("JWT_EXP_SECONDS", 86400))  # 1 day default

def create_token(user_id: str):
    payload = {
        "sub": str(user_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXP_SECONDS
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_token(token: str):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return data.get("sub")
    except Exception:
        return None
