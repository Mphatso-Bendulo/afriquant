"""
generate_sample_data.py
------------------------
Creates 8 placeholder CSV files in data/raw/, one per AfriQuant indicator.
This lets us test pipeline.py end-to-end BEFORE real data is collected.
Once real data is ready, replace these files (keep the same filename and
column names: date, value) and pipeline.py will work unchanged.

Run this ONCE, from the project's root folder:
    python generate_sample_data.py
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)  # so the fake numbers are the same every time we run this

# 24 months of dummy data: Jan 2023 -> Dec 2024
dates = pd.date_range(start="2023-01-01", periods=24, freq="MS")

# Each entry: (filename, starting_value, monthly_drift, monthly_noise)
INDICATORS = {
    "cpi_inflation.csv":     (28.0, 0.10, 1.0),
    "policy_rate.csv":       (24.0, 0.05, 0.3),
    "exchange_rate.csv":     (1050, 15.0, 8.0),
    "maize_price.csv":       (350, 5.0, 20.0),
    "fuel_price.csv":        (1800, 10.0, 30.0),
    "gdp_growth.csv":        (2.0, 0.02, 0.4),
    "tobacco_export.csv":    (150, 1.0, 10.0),
    "forex_reserves.csv":    (400, -2.0, 15.0),
}

os.makedirs("data/raw", exist_ok=True)

for filename, (start, drift, noise) in INDICATORS.items():
    values = start + drift * np.arange(24) + np.random.normal(0, noise, 24)
    df = pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "value": values.round(2)
    })
    path = os.path.join("data/raw", filename)
    df.to_csv(path, index=False)
    print(f"Created {path} ({len(df)} rows)")

print("\nDone. All 8 placeholder files are in data/raw/.")