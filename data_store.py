from __future__ import annotations
from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR  / "expenses.csv"
COLUMNS = ["date", "category", "amount", "notes"]

def _init_csv_if_needed() -> None:
       if not CSV_PATH.exists():
          pd.DataFrame(columns=COLUMNS).to_csv(CSV_PATH, index=False)

def load_expenses() -> pd.DataFrame:
    
    _init_csv_if_needed()
    df = pd.read_csv(CSV_PATH)

    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    df['date'] = pd.to_datetime(df["date"], errors="coerce")
    df['category']= df["category"].astype("string")
    df['notes'] = df['notes'].astype("string")
    df['amount'] = pd.to_numeric(df['amount'] , errors="coerce")
    #  drop any corrupted rows quietly
    return df.dropna(subset=['date', 'category', 'amount'])

def add_expense(date, category:str, amount:float, notes:str = "") -> None:
     
     if amount is None or pd.isna(amount) or amount < 0:
          raise ValueError("Amount must be a positive number")
     row = pd.DataFrame([{
          "date": pd.to_datetime(date).date(),
          "category": str(category),
          "amount": float(amount),
          "notes": str(notes or "")
     }], columns=COLUMNS)
     _init_csv_if_needed()
     row.to_csv(CSV_PATH, mode="a", header=not CSV_PATH.stat().st_size, index=False)

def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:

     if df.empty:
          return df
     temp = df.copy()
     temp['year_month'] = temp['date'].dt.to_period('M').astype(str)
     return (
          temp.groupby('year_month', as_index=False)['amount']
          .sum()
          .rename(columns ={"amount": "total_spend"})
          .sort_values("year_month")
     )



def category_breakdown(df: pd.DataFrame) -> pd.DataFrame:
     
     if df.empty:
          return df
     breakdown = (
          df.groupby('category', as_index=False)['amount']
          .sum()
          .rename(columns={"amount": "total_spend"})
          .sort_values("total_spend", ascending=False)
     )

     total = breakdown['total_spend'].sum()
     breakdown['percentage'] = (breakdown['total_spend'] / total * 100).round(2)
     
     return breakdown