import os
from pymongo import MongoClient, errors
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGODB_URI")
MONGO_DB = os.getenv("MONGODB_DB")

users_col = None
expenses_col = None

if not MONGO_URI:
    raise ValueError("❌ MONGODB_URI is missing from .env")
if not MONGO_DB:
    raise ValueError("❌ MONGODB_DB is missing from .env")

try:
    client = MongoClient(MONGO_URI)
    client.server_info()  # test connection
    db = client[MONGO_DB]

    users_col = db["users"]
    expenses_col = db["expenses"]

    print("✅ Connected to MongoDB successfully!")

except errors.ServerSelectionTimeoutError as e:
    raise RuntimeError("❌ Could not connect to MongoDB:", e)
except errors.OperationFailure as e:
    raise RuntimeError("❌ Authentication failed:", e)
