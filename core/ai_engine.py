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
        df["amount"] = (
            df["amount"].astype(str)
            .str.replace(r"[₱,\s]", "", regex=True)
        )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df[df["amount"] > 0].copy()
    df["date"] = pd.to_datetime(
        df["date"], dayfirst=True, errors="coerce"
    )
    df.dropna(subset=["date"], inplace=True)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def aggregate_monthly(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["amount"].sum().reset_index()
    monthly["ds"] = monthly["month"].dt.to_timestamp()
    monthly = monthly.rename(
        columns={"amount": "y"}
    )[["ds", "y"]]
    return monthly


def aggregate_by_category(df):
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby(
        ["month", "category"]
    )["amount"].sum().reset_index()


SKLEARN_FEATURE_COLS = [
    "month_sin", "month_cos",
    "is_feast_month", "is_christmas",
    "is_holy_week", "is_new_year"
]


def build_features(monthly_df, feast_days):
    df = monthly_df.copy()
    df["month_num"]      = df["ds"].dt.month
    df["month_sin"]      = np.sin(
        2 * np.pi * df["month_num"] / 12
    )
    df["month_cos"]      = np.cos(
        2 * np.pi * df["month_num"] / 12
    )
    df["year_month"]     = df["ds"].dt.to_period("M")
    feast_months         = (
        feast_days["ds"].dt.to_period("M").unique()
    )
    df["is_feast_month"] = (
        df["year_month"].isin(feast_months).astype(int)
    )
    df["is_christmas"]   = (
        (df["month_num"] == 12).astype(int)
    )
    df["is_holy_week"]   = (
        (df["month_num"] == 3).astype(int)
    )
    df["is_new_year"]    = (
        (df["month_num"] == 1).astype(int)
    )
    df.drop(columns=["year_month"], inplace=True)
    return df


def train_sklearn(df_features):
    X     = df_features[SKLEARN_FEATURE_COLS]
    y     = df_features["y"]
    model = LinearRegression()
    model.fit(X, y)
    return model


def forecast_sklearn(model, months_ahead, feast_days):
    last_date    = pd.Timestamp.today().to_period(
        "M"
    ).to_timestamp()
    future_dates = pd.date_range(
        start=last_date,
        periods=months_ahead + 1,
        freq="MS"
    )[1:]
    future_df    = pd.DataFrame(
        {"ds": future_dates, "y": 0.0}
    )
    future_df    = build_features(future_df, feast_days)
    X_future                = future_df[SKLEARN_FEATURE_COLS]
    future_df["yhat"]       = model.predict(X_future)
    future_df["yhat_lower"] = future_df["yhat"] * 0.80
    future_df["yhat_upper"] = future_df["yhat"] * 1.20
    return future_df[[
        "ds", "yhat", "yhat_lower", "yhat_upper"
    ]]


MODEL_PATH         = "core/model.pkl"
EXPENSE_MODEL_PATH = "core/expense_model.pkl"

EXPENSE_CATEGORIES = [
    "Building Maintenance", "Utilities", "Salaries",
    "Events", "Supplies", "Emergency", "Other"
]


class AIEngine:

    def __init__(self, db_manager):
        self.db             = db_manager
        self._model         = None
        self._expense_model = None
        self.feast_days     = build_feast_days()

    # ─── INCOME FORECAST ──────────────────────────────

    def run_forecast(self, months_ahead=6):
        raw_df   = self.db.get_historical_data()
        monthly  = aggregate_monthly(raw_df)
        n_months = len(monthly)

        if n_months < 3:
            return {
                "error": "Not enough data. Need at least 3 months."
            }

        model       = self._get_or_train(monthly)
        forecast_df = forecast_sklearn(
            model, months_ahead, self.feast_days
        )

        latest_actual   = monthly["y"].iloc[-1]
        latest_forecast = forecast_df["yhat"].iloc[0]
        variance_pct    = round(
            (latest_actual - latest_forecast) /
            latest_forecast * 100, 1
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
                "Low Collection Warning: collections are "
                "tracking below forecast."
                if alert else
                "Collections are on track."
            ),
        }

    # ─── EXPENSE FORECAST ─────────────────────────────

    def run_expense_forecast(self, months_ahead=6):
        expense_df = self.db.get_expense_historical_data()

        if expense_df.empty or len(expense_df) < 3:
            return {
                "error": "Not enough expense data for forecasting."
            }

        monthly_exp = aggregate_monthly(expense_df)

        if len(monthly_exp) < 3:
            return {
                "error": "Need at least 3 months of expense data."
            }

        model       = self._get_or_train_expense(monthly_exp)
        forecast_df = forecast_sklearn(
            model, months_ahead, self.feast_days
        )

        return {
            "monthly_df":  monthly_exp,
            "forecast_df": forecast_df,
        }

    # ─── FINANCIAL HEALTH CHECK ───────────────────────

    def check_financial_health(self, proposed_expense=0):
        balance     = self.db.get_net_balance()
        net_balance = balance["balance"]
        income      = balance["income"]
        expenses    = balance["expenses"]

        warnings = []

        if net_balance < 0:
            warnings.append({
                "level":   "CRITICAL",
                "message": (
                    "Parish balance is NEGATIVE. "
                    "Expenses exceed income by "
                    "₱{:,.0f}.".format(abs(net_balance))
                )
            })
        elif net_balance < (income * 0.10):
            warnings.append({
                "level":   "HIGH",
                "message": (
                    "Balance is critically low — "
                    "less than 10% of total income remaining."
                )
            })
        elif net_balance < (income * 0.20):
            warnings.append({
                "level":   "MEDIUM",
                "message": (
                    "Balance is below 20% of income. "
                    "Consider limiting new expenses."
                )
            })

        if proposed_expense > 0:
            after_expense = net_balance - proposed_expense
            if after_expense < 0:
                warnings.append({
                    "level":   "CRITICAL",
                    "message": (
                        "Cannot approve — this expense of "
                        "₱{:,.0f} exceeds available balance "
                        "of ₱{:,.0f}.".format(
                            proposed_expense, net_balance
                        )
                    )
                })
            elif after_expense < (income * 0.10):
                warnings.append({
                    "level":   "HIGH",
                    "message": (
                        "Approving this expense will leave "
                        "only ₱{:,.0f} in the balance.".format(
                            after_expense
                        )
                    )
                })

        expense_result = self.run_expense_forecast()
        income_result  = self.run_forecast()

        if ("error" not in expense_result and
                "error" not in income_result):
            exp_forecast = (
                expense_result["forecast_df"]["yhat"].mean()
            )
            inc_forecast = (
                income_result["forecast_df"]["yhat"].mean()
            )

            if exp_forecast > inc_forecast:
                warnings.append({
                    "level":   "HIGH",
                    "message": (
                        "ML forecast shows expenses will exceed "
                        "income in the next 6 months."
                    )
                })
            elif exp_forecast > (inc_forecast * 0.80):
                warnings.append({
                    "level":   "MEDIUM",
                    "message": (
                        "Expense forecast is reaching 80% of "
                        "income forecast. Monitor spending."
                    )
                })

        return {
            "net_balance":   net_balance,
            "income":        income,
            "expenses":      expenses,
            "warnings":      warnings,
            "safe_to_spend": (
                net_balance > (income * 0.20) and
                not any(
                    w["level"] == "CRITICAL"
                    for w in warnings
                )
            )
        }

    # ─── AUTO RETRAIN ─────────────────────────────────

    def retrain_if_needed(self):
        """Called automatically after every new donation save."""
        for path in [MODEL_PATH, EXPENSE_MODEL_PATH]:
            if os.path.exists(path):
                os.remove(path)
        self._model         = None
        self._expense_model = None

    def retrain(self):
        self.retrain_if_needed()

    # ─── INTERNAL HELPERS ─────────────────────────────

    def _get_or_train(self, monthly):
        if self._model is not None:
            return self._model
        saved = self._load_model(MODEL_PATH)
        if saved:
            self._model = saved
            return saved
        df_features = build_features(monthly, self.feast_days)
        model       = train_sklearn(df_features)
        self._model = model
        self._save_model(model, MODEL_PATH)
        return model

    def _get_or_train_expense(self, monthly):
        if self._expense_model is not None:
            return self._expense_model
        saved = self._load_model(EXPENSE_MODEL_PATH)
        if saved:
            self._expense_model = saved
            return saved
        df_features          = build_features(
            monthly, self.feast_days
        )
        model                = train_sklearn(df_features)
        self._expense_model  = model
        self._save_model(model, EXPENSE_MODEL_PATH)
        return model

    def _save_model(self, model, path):
        os.makedirs("core", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(model, f)

    def _load_model(self, path):
        if os.path.exists(path):
            with open(path, "rb") as f:
                return pickle.load(f)
        return None