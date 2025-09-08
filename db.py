# db.py
import os
from pymongo import MongoClient, errors
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB")

if not MONGO_URI:
    raise ValueError("❌ MONGODB_URI is missing from .env")

if not MONGO_DB:
    raise ValueError("❌ MONGODB_DB is missing from .env")

try:
    client = MongoClient(MONGO_URI)
    # Force connection test
    client.server_info()
    print("✅ Connected to MongoDB Atlas!")
    db = client[MONGO_DB]

    # Collections
    users_col = db["users"]
    expenses_col = db["expenses"]

except errors.ServerSelectionTimeoutError as e:
    print("❌ Could not connect to MongoDB (timeout):", e)
    raise e
except errors.OperationFailure as e:
    print("❌ Authentication failed, check your username/password:", e)
    raise e

