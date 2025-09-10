import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import ElasticNet
from xgboost import XGBRegressor
import joblib
from data_store import monthly_summary

def train_model(user_id: str):
    msum = monthly_summary(user_id)
    if msum.empty or len(msum) < 3:
        raise ValueError("❌ Not enough data to train a model")

    msum['year_month'] = pd.to_datetime(msum["year_month"])
    msum['month_num'] = msum['year_month'].dt.month
    msum['year'] = msum['year_month'].dt.year
    msum['lag_1'] = msum['total_spend'].shift(1)
    msum['rolling_3'] = msum['total_spend'].rolling(window=3).mean()
    msum = msum.dropna()

    X = msum[["month_num", "year", "lag_1", "rolling_3"]]
    y = msum["total_spend"]

    if len(X) < 3:
        raise ValueError("❌ Need at least 3 months of data after feature engineering")

    test_size = 0.2 if len(X) > 5 else 0.33
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, shuffle=False)

    enet = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42)
    enet.fit(X_train, y_train)
    enet_rmse = np.sqrt(mean_squared_error(y_test, enet.predict(X_test)))
    enet_r2 = r2_score(y_test, enet.predict(X_test))

    xgb = XGBRegressor(
        n_estimators=500, learning_rate=0.05, max_depth=3,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )
    xgb.fit(X_train, y_train)
    xgb_rmse = np.sqrt(mean_squared_error(y_test, xgb.predict(X_test)))
    xgb_r2 = r2_score(y_test, xgb.predict(X_test))

    best_model = xgb if xgb_rmse < enet_rmse else enet

    os.makedirs("models", exist_ok=True)
    joblib.dump(best_model, f"models/model_{user_id}.pkl")

    return {
        "model": best_model,
        "enet_r2": enet_r2,
        "enet_rmse": enet_rmse,
        "xgb_r2": xgb_r2,
        "xgb_rmse": xgb_rmse
    }
