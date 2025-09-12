
import numpy as np
import pandas as pd
from sklearn.linear_model import ElasticNet
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor

from data_store import monthly_summary

def _make_features(msum: pd.DataFrame):
    m = msum.copy()
    m["year_month"] = pd.to_datetime(m["year_month"])
    m["month_num"] = m["year_month"].dt.month
    m["year"] = m["year_month"].dt.year
    m["lag_1"] = m["total_spend"].shift(1)
    m["rolling_3"] = m["total_spend"].rolling(3).mean()
    m = m.dropna().reset_index(drop=True)
    X = m[["month_num", "year", "lag_1", "rolling_3"]]
    y = m["total_spend"]
    return X, y

def train_model(user_id: str):
    msum = monthly_summary(user_id)
    if msum.empty or len(msum) < 4:
        raise ValueError("Not enough monthly data to train (need at least 4 months).")

    X, y = _make_features(msum)
    if X.empty:
        raise ValueError("After feature engineering, no training rows remain.")

    
    n = len(X)
    split = max(1, int(n * 0.8))
    X_train, X_val = X.iloc[:split], X.iloc[split:]
    y_train, y_val = y.iloc[:split], y.iloc[split:]

    # ElasticNet
    en = ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42, max_iter=5000)
    en.fit(X_train, y_train)
    en_pred = en.predict(X_val)
    en_rmse = np.sqrt(mean_squared_error(y_val, en_pred))

    # XGBoost
    xgb = XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=3, random_state=42, n_jobs=1)
    xgb.fit(X_train, y_train)
    xgb_pred = xgb.predict(X_val)
    xgb_rmse = np.sqrt(mean_squared_error(y_val, xgb_pred))

    
    if xgb_rmse <= en_rmse:
        best = xgb
        best_name = "xgboost"
        best_rmse = xgb_rmse
    else:
        best = en
        best_name = "elasticnet"
        best_rmse = en_rmse

    return {"model": best, "model_name": best_name, "rmse": float(best_rmse)}
