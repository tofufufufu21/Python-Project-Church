import pandas as pd
import numpy as np
import pickle
import os
from sklearn.linear_model import LinearRegression


def build_feast_days():
    rows = []
    for year in range(2023, 2028):
        rows += [
            {"holiday": "Christmas",     "ds": str(year) + "-12-25"},
            {"holiday": "New Year",      "ds": str(year) + "-01-01"},
            {"holiday": "Holy Week",     "ds": str(year) + "-03-28"},
            {"holiday": "All Souls",     "ds": str(year) + "-11-02"},
            {"holiday": "Parish Fiesta", "ds": str(year) + "-06-15"},
        ]
    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["ds"])
    return df


def load_from_excel(filepath):
    df = pd.read_excel(filepath)
    df.columns = df.columns.str.strip().str.lower()
    df.rename(columns={
        "date of collection": "date",
        "donation":           "amount",
        "offering amount":    "amount",
        "type":               "category",
    }, inplace=True)
    df.dropna(subset=["date", "amount"], inplace=True)
    if df["amount"].dtype == object:
        df["amount"] = df["amount"].astype(str).str.replace(r"[₱,\s]", "", regex=True)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df[df["amount"] > 0].copy()
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def aggregate_monthly(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly["ds"] = monthly["month"].dt.to_timestamp()
    monthly = monthly.rename(columns={"amount": "y"})[["ds", "y"]]
    return monthly


def aggregate_by_category(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby(["month", "category"])["amount"].sum().reset_index()


SKLEARN_FEATURE_COLS = [
    "month_sin", "month_cos",
    "is_feast_month", "is_christmas", "is_holy_week", "is_new_year"
]


def build_features(monthly_df, feast_days):
    df = monthly_df.copy()
    df["month_num"]      = df["ds"].dt.month
    df["month_sin"]      = np.sin(2 * np.pi * df["month_num"] / 12)
    df["month_cos"]      = np.cos(2 * np.pi * df["month_num"] / 12)
    df["year_month"]     = df["ds"].dt.to_period("M")
    feast_months         = feast_days["ds"].dt.to_period("M").unique()
    df["is_feast_month"] = df["year_month"].isin(feast_months).astype(int)
    df["is_christmas"]   = (df["month_num"] == 12).astype(int)
    df["is_holy_week"]   = (df["month_num"] == 3).astype(int)
    df["is_new_year"]    = (df["month_num"] == 1).astype(int)
    df.drop(columns=["year_month"], inplace=True)
    return df


def train_sklearn(df_features):
    X = df_features[SKLEARN_FEATURE_COLS]
    y = df_features["y"]
    model = LinearRegression()
    model.fit(X, y)
    return model


def forecast_sklearn(model, months_ahead, feast_days):
    last_date    = pd.Timestamp.today().to_period("M").to_timestamp()
    future_dates = pd.date_range(start=last_date, periods=months_ahead + 1, freq="MS")[1:]
    future_df    = pd.DataFrame({"ds": future_dates, "y": 0.0})
    future_df    = build_features(future_df, feast_days)
    X_future                = future_df[SKLEARN_FEATURE_COLS]
    future_df["yhat"]       = model.predict(X_future)
    future_df["yhat_lower"] = future_df["yhat"] * 0.80
    future_df["yhat_upper"] = future_df["yhat"] * 1.20
    return future_df[["ds", "yhat", "yhat_lower", "yhat_upper"]]


MODEL_PATH = "core/model.pkl"


class AIEngine:

    def __init__(self, db_manager):
        self.db         = db_manager
        self._model     = None
        self.feast_days = build_feast_days()

    def run_forecast(self, months_ahead=6):
        raw_df   = self.db.get_historical_data()
        monthly  = aggregate_monthly(raw_df)
        n_months = len(monthly)
        if n_months < 3:
            return {"error": "Not enough data. Need at least 3 months of records."}
        model       = self._get_or_train(monthly)
        forecast_df = forecast_sklearn(model, months_ahead, self.feast_days)
        latest_actual   = monthly["y"].iloc[-1]
        latest_forecast = forecast_df["yhat"].iloc[0]
        variance_pct    = round(
            (latest_actual - latest_forecast) / latest_forecast * 100, 1
        )
        alert = latest_actual < (latest_forecast * 0.80)
        return {
            "model_type":    "sklearn",
            "n_months":      n_months,
            "monthly_df":    monthly,
            "forecast_df":   forecast_df,
            "category_df":   aggregate_by_category(raw_df),
            "variance_pct":  variance_pct,
            "alert":         alert,
            "alert_message": (
                "Low Collection Warning: collections are tracking below forecast."
                if alert else "Collections are on track."
            ),
        }

    def retrain(self):
        if os.path.exists(MODEL_PATH):
            os.remove(MODEL_PATH)
        self._model = None

    def _get_or_train(self, monthly):
        if self._model is not None:
            return self._model
        saved = self._load_model()
        if saved:
            self._model = saved
            return saved
        df_features = build_features(monthly, self.feast_days)
        model       = train_sklearn(df_features)
        self._model = model
        self._save_model(model)
        return model

    def _save_model(self, model):
        os.makedirs("core", exist_ok=True)
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)

    def _load_model(self):
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                return pickle.load(f)
        return None