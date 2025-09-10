# data_store.py
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pandas as pd

from db import users_col, expenses_col


# ---------------- USER MANAGEMENT ----------------
def create_user(username: str, password: str):
    if users_col.find_one({"username": username}):
        raise ValueError("❌ Username already exists")

    hashed_pw = generate_password_hash(password)
    user = {"username": username, "password": hashed_pw}
    result = users_col.insert_one(user)
    return str(result.inserted_id)


def verify_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if user and check_password_hash(user["password"], password):
        return str(user["_id"])
    return None


# ---------------- EXPENSES ----------------
def add_expense(user_id: str, date, category: str, amount: float, notes: str = ""):
    """Insert a new expense into DB"""

    # Ensure valid user_id type
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise ValueError("❌ Invalid user_id format")

    # Ensure date is datetime (Streamlit gives datetime.date)
    if not isinstance(date, datetime):
        date = datetime.combine(date, datetime.min.time())

    expense = {
        "user_id": user_oid,
        "date": date,
        "category": category,
        "amount": float(amount),
        "notes": notes,
        "created_at": datetime.utcnow()
    }
    expenses_col.insert_one(expense)


def load_expenses(user_id: str) -> pd.DataFrame:
    """Load user expenses as DataFrame without exposing internal fields"""
    cursor = expenses_col.find({"user_id": ObjectId(user_id)})
    df = pd.DataFrame(list(cursor))

    if not df.empty:
        df.drop(columns=["_id", "user_id", "created_at"], errors="ignore", inplace=True)
        df["date"] = pd.to_datetime(df["date"])

    return df


# ---------------- ANALYTICS ----------------
def monthly_summary(user_id: str) -> pd.DataFrame:
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {
            "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
            "total_spend": {"$sum": "$amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    result = list(expenses_col.aggregate(pipeline))

    df = pd.DataFrame(result)
    if not df.empty:
        df["year_month"] = pd.to_datetime(df["_id"].apply(
            lambda x: f"{x['year']}-{x['month']:02d}"
        ))
        df = df[["year_month", "total_spend"]]

    return df


def category_breakdown(user_id: str) -> pd.DataFrame:
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {"$group": {"_id": "$category", "total_spend": {"$sum": "$amount"}}}
    ]
    result = list(expenses_col.aggregate(pipeline))

    df = pd.DataFrame(result)
    if not df.empty:
        df.rename(columns={"_id": "category"}, inplace=True)

    return df
