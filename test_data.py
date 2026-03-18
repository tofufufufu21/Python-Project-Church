import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.ai_engine import (
    load_from_excel,
    aggregate_monthly,
    aggregate_by_category,
    build_feast_days,
    build_features,
    train_sklearn,
    forecast_sklearn
)

print("==============================================")
print("  CHURCHTRACK ML TEST")
print("==============================================")

print("")
print("TEST 1 - Loading Excel file...")
df = load_from_excel("church_data.xlsx")
print("PASSED - Rows loaded: " + str(len(df)))
print("Columns: " + str(df.columns.tolist()))

print("")
print("TEST 2 - First 5 rows:")
print(df.head())

print("")
print("TEST 3 - Monthly totals:")
monthly = aggregate_monthly(df)
print(monthly)

print("")
print("TEST 4 - Category breakdown:")
category_df = aggregate_by_category(df)
print(category_df.groupby("category")["amount"].sum().sort_values(ascending=False))

print("")
print("TEST 5 - Building ML features...")
feast_days = build_feast_days()
features = build_features(monthly, feast_days)
print("PASSED - Features shape: " + str(features.shape))

print("")
print("TEST 6 - Training ML model...")
model = train_sklearn(features)
print("PASSED - Model trained successfully")

print("")
print("TEST 7 - Generating 6 month forecast...")
forecast = forecast_sklearn(model, 6, feast_days)
print("PASSED - Forecast output:")
print(forecast)

print("")
print("TEST 8 - Budget alert check...")
latest_actual   = monthly["y"].iloc[-1]
latest_forecast = forecast["yhat"].iloc[0]
variance_pct    = round((latest_actual - latest_forecast) / latest_forecast * 100, 1)
alert           = latest_actual < (latest_forecast * 0.80)
print("Latest actual:   " + str(latest_actual))
print("Latest forecast: " + str(round(latest_forecast, 2)))
print("Variance:        " + str(variance_pct) + "%")
print("Alert triggered: " + str(alert))

print("")
print("==============================================")
print("  ALL TESTS DONE - ML IS WORKING")
print("==============================================")


