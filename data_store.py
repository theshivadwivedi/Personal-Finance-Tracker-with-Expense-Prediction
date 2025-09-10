import pandas as pd
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

from db import users_col, expenses_col

# ---------------- USER MANAGEMENT ----------------
def create_user(username: str, password: str):
    if users_col.find_one({"username": username}):
        raise ValueError("❌ Username already exists")
    hashed_pw = generate_password_hash(password)
    result = users_col.insert_one({
        "username": username,
        "password": hashed_pw,
        "created_at": datetime.utcnow()
    })
    return str(result.inserted_id)

def verify_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if not user:
        return None
    stored_pw = user.get("password") or user.get("password_hash")
    if stored_pw and check_password_hash(stored_pw, password):
        return str(user["_id"])
    return None

# ---------------- EXPENSES ----------------
def add_expense(user_id: str, expense_date, category: str, amount: float, notes: str = ""):
    try:
        user_oid = ObjectId(user_id)
    except Exception:
        raise ValueError("❌ Invalid user_id format")

    if isinstance(expense_date, date) and not isinstance(expense_date, datetime):
        expense_date = datetime.combine(expense_date, datetime.min.time())

    expenses_col.insert_one({
        "user_id": user_oid,
        "date": expense_date,
        "category": category,
        "amount": float(amount),
        "notes": notes,
        "created_at": datetime.utcnow()
    })

def load_expenses(user_id: str) -> pd.DataFrame:
    try:
        user_oid = ObjectId(user_id)
        cursor = expenses_col.find({"user_id": user_oid})
        df = pd.DataFrame(list(cursor))

        if not df.empty:
            df.drop(columns=["_id", "user_id", "created_at"], errors="ignore", inplace=True)
            df["date"] = pd.to_datetime(df["date"])

        return df
    except Exception as e:
        print("⚠️ load_expenses error:", e)
        return pd.DataFrame()

# ---------------- ANALYTICS ----------------
def monthly_summary(user_id: str) -> pd.DataFrame:
    try:
        user_oid = ObjectId(user_id)
        pipeline = [
            {"$match": {"user_id": user_oid}},
            {"$group": {
                "_id": {"year": {"$year": "$date"}, "month": {"$month": "$date"}},
                "total_spend": {"$sum": "$amount"}
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}}
        ]
        result = list(expenses_col.aggregate(pipeline))
        df = pd.DataFrame(result)
        if not df.empty:
            df["year_month"] = pd.to_datetime(df["_id"].apply(lambda x: f"{x['year']}-{x['month']:02d}"))
            df = df[["year_month", "total_spend"]]
        return df
    except Exception as e:
        print("⚠️ monthly_summary error:", e)
        return pd.DataFrame()

def category_breakdown(user_id: str) -> pd.DataFrame:
    try:
        user_oid = ObjectId(user_id)
        pipeline = [
            {"$match": {"user_id": user_oid}},
            {"$group": {"_id": "$category", "total_spend": {"$sum": "$amount"}}}
        ]
        result = list(expenses_col.aggregate(pipeline))
        df = pd.DataFrame(result)
        if not df.empty:
            df.rename(columns={"_id": "category"}, inplace=True)
        return df
    except Exception as e:
        print("⚠️ category_breakdown error:", e)
        return pd.DataFrame()
