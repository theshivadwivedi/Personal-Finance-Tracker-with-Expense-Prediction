import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import ElasticNet
from xgboost import XGBRegressor
import joblib
from data_store import load_expenses, monthly_summary

# ---------------- Step 1: Load & Preprocess ----------------
df = load_expenses()
if df.empty:
    raise ValueError("No expense data found! Add data first.")

msum = monthly_summary(df)

# Feature Engineering
msum['year_month'] = pd.to_datetime(msum['year_month'])
msum['month_num'] = msum['year_month'].dt.month
msum['year'] = msum['year_month'].dt.year
msum['lag_1'] = msum['total_spend'].shift(1)
msum['lag_2'] = msum['total_spend'].shift(2)
msum['lag_3'] = msum['total_spend'].shift(3)
msum['rolling_3'] = msum['total_spend'].rolling(window=3).mean()
msum['rolling_6'] = msum['total_spend'].rolling(window=6).mean()
msum['is_quarter_end'] = (msum['month_num'] % 3 == 0).astype(int)
msum['is_year_start'] = (msum['month_num'] == 1).astype(int)

msum = msum.dropna()
if msum.empty:
    raise ValueError("Not enough data. Please add more expenses.")

X = msum.drop(columns=['year_month', 'total_spend'])
y = msum['total_spend']

# ---------------- Step 2: ElasticNet Baseline ----------------
enet = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
tscv = TimeSeriesSplit(n_splits=5)

enet_rmse_scores = []
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    enet.fit(X_train, y_train)
    pred = enet.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, pred))
    enet_rmse_scores.append(rmse)

enet_rmse = np.mean(enet_rmse_scores)
print(f"ElasticNet CV RMSE: {enet_rmse:.2f}")

# ---------------- Step 3: XGBoost with GridSearch ----------------
xgb = XGBRegressor(objective="reg:squarederror", random_state=42)

param_grid = {
    "n_estimators": [200, 500, 800],
    "max_depth": [3, 4, 6],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.7, 0.8, 1.0],
    "colsample_bytree": [0.7, 0.8, 1.0],
}

grid = GridSearchCV(
    estimator=xgb,
    param_grid=param_grid,
    scoring="neg_root_mean_squared_error",
    cv=TimeSeriesSplit(n_splits=5),
    n_jobs=-1,
    verbose=1,
)

grid.fit(X, y)
best_xgb = grid.best_estimator_
xgb_rmse = -grid.best_score_

print(f"XGBoost CV RMSE: {xgb_rmse:.2f} (best params: {grid.best_params_})")

# ---------------- Step 4: Select Best Model ----------------
if xgb_rmse <= enet_rmse:
    best_model = best_xgb
    best_name = "xgboost"
    best_rmse = xgb_rmse
else:
    best_model = enet
    best_name = "elasticnet"
    best_rmse = enet_rmse

print(f"\n✅ Best model: {best_name} (RMSE={best_rmse:.2f})")

# ---------------- Step 5: Save ----------------
joblib.dump(best_model, "model.pkl")
print("📦 Model saved as model.pkl")
