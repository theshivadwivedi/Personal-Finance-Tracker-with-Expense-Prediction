import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Generate dates (2 years daily)
dates = pd.date_range(start="2023-01-01", end="2025-01-01", freq="D")

categories = ["Rent", "Food", "Transport", "Health", "Entertainment", "Bills", "Miscellaneous"]
data = []

for date in dates:
    month = date.month
    
    # Rent (once per month, fixed ~1000)
    if date.day == 1:
        data.append([date, "Rent", 1000 + np.random.randint(-50, 50), "Monthly rent"])
    
    # Food (almost every day, varies)
    if np.random.rand() < 0.7:
        amount = np.random.randint(600, 1500)
        data.append([date, "Food", amount, "Meals / groceries"])
    
    # Transport (random days)
    if np.random.rand() < 0.3:
        amount = np.random.randint(300, 800)
        data.append([date, "Transport", amount, "Bus/Taxi/Fuel"])
    
    # Health (occasional)
    if np.random.rand() < 0.05:
        amount = np.random.randint(500, 2000)
        data.append([date, "Health", amount, "Doctor/medicine"])
    
    # Entertainment (weekends mostly)
    if date.weekday() >= 5 and np.random.rand() < 0.5:
        amount = np.random.randint(400, 1200)
        data.append([date, "Entertainment", amount, "Movies / fun"])
    
    # Bills (once per month)
    if date.day == 5:
        amount = np.random.randint(600, 1000)
        data.append([date, "Bills", amount, "Electricity / Internet"])
    
    # Miscellaneous (random small)
    if np.random.rand() < 0.2:
        amount = np.random.randint(100, 500)
        data.append([date, "Miscellaneous", amount, "Random spend"])

# Convert to DataFrame
df = pd.DataFrame(data, columns=["date", "category", "amount", "notes"])

# Save as CSV
df.to_csv("data/expenses.csv", index=False)

print("✅ Generated synthetic dataset with", len(df), "rows")
