import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "FinanceApp")

client = None
db = None
users_col = None
expenses_col = None

try:
    if not MONGODB_URI:
        raise ValueError("MONGODB_URI is missing")

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # force connection test

    db = client[MONGODB_DB]
    users_col = db["users"]
    expenses_col = db["expenses"]

except Exception as e:
    # Streamlit-specific graceful fail
    try:
        import streamlit as st
        st.warning(f"⚠️ Could not connect to MongoDB: {e}")
    except ImportError:
        print(f"❌ MongoDB connection failed: {e}")

