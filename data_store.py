
# data_store.py
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import pandas as pd
from db import users_col, expenses_col

# ---------------- USER MANAGEMENT ----------------
def create_user(username: str, password: str):
    if users_col.find_one({"username": username}):
        raise ValueError("❌ Username already exists")
    if not password or len(password) < 4:
        raise ValueError("❌ Password too short")

    hashed_pw = generate_password_hash(password)
    user = {"username": username.strip(), "password": hashed_pw}
    result = users_col.insert_one(user)
    return str(result.inserted_id)

def verify_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if not user or "password" not in user:
        return None
    try:
        if check_password_hash(user["password"], password):
            return str(user["_id"])
    except Exception:
        return None
    return None

# ---------------- EXPENSES ----------------
def add_expense(user_id: str, expense_date, category: str, amount: float, notes: str = ""):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise ValueError("❌ Invalid user_id format")

    if amount <= 0:
        raise ValueError("❌ Amount must be positive")

    if isinstance(expense_date, date) and not isinstance(expense_date, datetime):
        expense_date = datetime.combine(expense_date, datetime.min.time())

    expense = {
        "user_id": user_oid,
        "date": expense_date,
        "category": category.strip().title(),
        "amount": float(amount),
        "notes": notes.strip(),
        "created_at": datetime.utcnow()
    }
    expenses_col.insert_one(expense)

def load_expenses(user_id: str) -> pd.DataFrame:
    cursor = expenses_col.find({"user_id": ObjectId(user_id)})
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df.drop(columns=["_id", "user_id", "created_at"], errors="ignore", inplace=True)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
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
