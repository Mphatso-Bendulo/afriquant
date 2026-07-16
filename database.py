"""
database.py
------------
AfriQuant Phase 4: SQLite storage layer.

Reads data/output/master.csv (produced by pipeline.py) and loads it
into a SQLite database at data/output/afriquant.db.

Schema (see AfriQuant Handbook, Section 5.3):
  indicators   -- one row per indicator (name, unit)
  observations -- one row per indicator per date (value + derived metrics)

This is idempotent: running it twice with the same master.csv produces
the same database contents, not duplicates (Handbook Section 4.3).

Run this AFTER pipeline.py, from the project's root folder:
    python database.py
"""

import sqlite3
import pandas as pd
import os

MASTER_FILE = "data/output/master.csv"
DB_FILE = "data/output/afriquant.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS indicators (
    indicator TEXT PRIMARY KEY,
    indicator_name TEXT NOT NULL,
    unit TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL REFERENCES indicators(indicator),
    date TEXT NOT NULL,
    value REAL NOT NULL,
    mom_change REAL,
    yoy_change REAL,
    rolling_3m_avg REAL,
    UNIQUE(indicator, date)
);
"""


def load_master() -> pd.DataFrame:
    if not os.path.exists(MASTER_FILE):
        raise FileNotFoundError(f"Missing {MASTER_FILE}. Run `python pipeline.py` first.")
    return pd.read_csv(MASTER_FILE)


def build_database():
    master = load_master()

    conn = sqlite3.connect(DB_FILE)
    conn.executescript(SCHEMA)

    # --- indicators table: one row per unique indicator ---
    indicators = master[["indicator", "indicator_name", "unit"]].drop_duplicates()
    conn.executemany(
        "INSERT OR REPLACE INTO indicators (indicator, indicator_name, unit) VALUES (?, ?, ?)",
        indicators.itertuples(index=False, name=None),
    )

    # --- observations table: one row per indicator per date ---
    obs_cols = ["indicator", "date", "value", "mom_change", "yoy_change", "rolling_3m_avg"]
    # Convert pandas NaN -> None so SQLite stores proper NULLs, not garbage
    observations = master[obs_cols].astype(object).where(pd.notna(master[obs_cols]), None)
    conn.executemany(
        """
        INSERT OR REPLACE INTO observations
            (indicator, date, value, mom_change, yoy_change, rolling_3m_avg)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        observations.itertuples(index=False, name=None),
    )

    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    print(f"Database ready at {DB_FILE} -- {count} observation rows loaded.")
    conn.close()


if __name__ == "__main__":
    build_database()