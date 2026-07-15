"""
pipeline.py
-----------
AfriQuant Phase 1 data pipeline.

Steps:
  1. Load each of the 8 indicator CSVs from data/raw/
  2. Standardise and validate the date column
  3. Compute month-over-month %, year-over-year %, and 3-month rolling average
  4. Merge all 8 indicators into one long-format master table
  5. Save the result to data/output/master.csv

Design principles (see AfriQuant Handbook, Section 4):
  - Modularity: each step is its own function
  - Fail loudly: bad data stops the pipeline with a clear error
  - Reproducibility: same inputs -> same output, every time

Run this from the project's root folder:
    python pipeline.py
"""

import pandas as pd
import os

RAW_DIR = "data/raw"
OUTPUT_DIR = "data/output"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "master.csv")

# indicator_key : (filename, display_name, unit)
INDICATORS = {
    "cpi_inflation":  ("cpi_inflation.csv",  "CPI Inflation",         "%"),
    "policy_rate":    ("policy_rate.csv",    "RBM Policy Rate",       "%"),
    "exchange_rate":  ("exchange_rate.csv",  "MWK/USD Exchange Rate", "MWK"),
    "maize_price":    ("maize_price.csv",    "Maize Price",           "MWK/kg"),
    "fuel_price":     ("fuel_price.csv",     "Fuel Price",            "MWK/litre"),
    "gdp_growth":     ("gdp_growth.csv",     "GDP Growth",            "%"),
    "tobacco_export": ("tobacco_export.csv", "Tobacco Export Value",  "USD millions"),
    "forex_reserves": ("forex_reserves.csv", "Forex Reserves",        "USD millions"),
}


def load_raw(filename: str) -> pd.DataFrame:
    """Load one indicator's raw CSV and check it has the columns we need."""
    path = os.path.join(RAW_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing raw file: {path}\n"
            f"-> Run generate_sample_data.py first, or add the real file."
        )

    df = pd.read_csv(path)
    required_cols = {"date", "value"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"{filename} must have columns {required_cols}, but has {list(df.columns)}"
        )
    return df


def standardise_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the date column to a real datetime, drop bad rows, and sort.
    Rebuilds a fresh DataFrame rather than mutating in place.
    """
    clean = pd.DataFrame({
        "date": pd.to_datetime(df["date"], errors="coerce"),
        "value": pd.to_numeric(df["value"], errors="coerce"),
    })

    bad_rows = clean["date"].isna() | clean["value"].isna()
    if bad_rows.any():
        print(f"  Warning: dropping {bad_rows.sum()} row(s) with bad date/value")
        clean = clean[~bad_rows]

    clean = clean.sort_values("date").reset_index(drop=True)

    if clean["date"].duplicated().any():
        raise ValueError("Duplicate dates found after cleaning -- check the raw file.")

    return clean


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add month-over-month %, year-over-year %, and 3-month rolling average."""
    df = df.copy()
    df["mom_change"] = df["value"].pct_change(1) * 100
    df["yoy_change"] = df["value"].pct_change(12) * 100
    df["rolling_3m_avg"] = df["value"].rolling(window=3).mean()
    return df


def build_master_table() -> pd.DataFrame:
    """Load, clean, and process all 8 indicators; merge into one long table."""
    all_frames = []
    for key, (filename, display_name, unit) in INDICATORS.items():
        print(f"Processing {display_name} ({filename})...")
        raw = load_raw(filename)
        clean = standardise_dates(raw)
        with_metrics = compute_metrics(clean)
        with_metrics["indicator"] = key
        with_metrics["indicator_name"] = display_name
        with_metrics["unit"] = unit
        all_frames.append(with_metrics)

    master = pd.concat(all_frames, ignore_index=True)
    column_order = [
        "date", "indicator", "indicator_name", "unit",
        "value", "mom_change", "yoy_change", "rolling_3m_avg",
    ]
    return master[column_order]


def main():
    print("=== AfriQuant Pipeline: starting ===\n")
    master = build_master_table()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    master.to_csv(OUTPUT_FILE, index=False)
    print(f"\n=== Done. {len(master)} rows written to {OUTPUT_FILE} ===")


if __name__ == "__main__":
    main()