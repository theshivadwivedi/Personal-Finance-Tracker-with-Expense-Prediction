import pandas as pd
import numpy as np


np.random.seed(42)


dates = pd.date_range(start="2023-01-01", end="2025-01-01", freq="D")

categories = ["Rent", "Food", "Transport", "Health", "Entertainment", "Bills", "Miscellaneous"]
data = []

for date in dates:
    month = date.month
    
    
    if date.day == 1:
        data.append([date, "Rent", 1000 + np.random.randint(-50, 50), "Monthly rent"])
    
    
    if np.random.rand() < 0.7:
        amount = np.random.randint(600, 1500)
        data.append([date, "Food", amount, "Meals / groceries"])
    
    
    if np.random.rand() < 0.3:
        amount = np.random.randint(300, 800)
        data.append([date, "Transport", amount, "Bus/Taxi/Fuel"])
    
   
    if np.random.rand() < 0.05:
        amount = np.random.randint(500, 2000)
        data.append([date, "Health", amount, "Doctor/medicine"])
    
    
    if date.weekday() >= 5 and np.random.rand() < 0.5:
        amount = np.random.randint(400, 1200)
        data.append([date, "Entertainment", amount, "Movies / fun"])
    
   
    if date.day == 5:
        amount = np.random.randint(600, 1000)
        data.append([date, "Bills", amount, "Electricity / Internet"])
    
    
    if np.random.rand() < 0.2:
        amount = np.random.randint(100, 500)
        data.append([date, "Miscellaneous", amount, "Random spend"])


df = pd.DataFrame(data, columns=["date", "category", "amount", "notes"])


df.to_csv("data/expenses.csv", index=False)

print("✅ Generated synthetic dataset with", len(df), "rows")
