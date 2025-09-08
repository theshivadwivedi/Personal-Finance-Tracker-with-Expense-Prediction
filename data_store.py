# data_store.py
from db import users_col, expenses_col
from bson import ObjectId
import pandas as pd
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# -------- USERS ----------
def create_user(username: str, password: str):
    if users_col.find_one({"username": username}):
        raise ValueError("Username already exists")
    result = users_col.insert_one({
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.utcnow()
    })
    return str(result.inserted_id)

def verify_user(username: str, password: str):
    user = users_col.find_one({"username": username})
    if user and check_password_hash(user["password_hash"], password):
        return str(user["_id"])
    return None

def get_user(user_id: str):
    return users_col.find_one({"_id": ObjectId(user_id)})

# -------- EXPENSES ----------
def add_expense(user_id: str, date, category: str, amount: float, notes: str = ""):
    expenses_col.insert_one({
        "user_id": ObjectId(user_id),
        "date": pd.to_datetime(date),
        "category": category,
        "amount": amount,
        "notes": notes,
        "created_at": datetime.utcnow()
    })

def load_expenses(user_id: str) -> pd.DataFrame:
    cursor = expenses_col.find(
        {"user_id": ObjectId(user_id)},
        {"_id": 0, "user_id": 0, "created_at": 0}  # exclude these fields
    )
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["date"] = df["date"].dt.normalize()
    return df


import pandas as pd

def monthly_summary(user_id: str) -> pd.DataFrame:
    df = load_expenses(user_id)
    if df.empty:
        return pd.DataFrame(columns=["year_month", "total_spend"])
    
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M").astype(str)

    monthly_df = df.groupby("year_month")["amount"].sum().reset_index(name="total_spend")
    
    return monthly_df



def category_breakdown(user_id: str) -> pd.DataFrame:
    df = load_expenses(user_id)
    if df.empty:
        return pd.DataFrame(columns=["category", "total_spend"])
    return df.groupby("category")["amount"].sum().reset_index(name="total_spend")
