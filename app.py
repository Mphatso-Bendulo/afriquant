"""
app.py
------
AfriQuant Phase 3: first interactive dashboard.
Reads data/output/master.csv (produced by pipeline.py) and displays it.

This does NOT recompute anything. It only reads and displays.
If a number looks wrong here, the bug is in pipeline.py, not here.

Run this from the project's root folder:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
import os

MASTER_FILE = "data/output/master.csv"

st.set_page_config(page_title="AfriQuant", layout="wide")


@st.cache_data
def load_master() -> pd.DataFrame:
    if not os.path.exists(MASTER_FILE):
        st.error(
            f"Can't find {MASTER_FILE}. Run `python pipeline.py` first "
            f"to generate it."
        )
        st.stop()
    df = pd.read_csv(MASTER_FILE, parse_dates=["date"])
    return df


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    """One row per indicator: its most recent value and mom_change."""
    latest = df.sort_values("date").groupby("indicator").tail(1)
    return latest[["indicator_name", "unit", "date", "value", "mom_change"]]


# ---------- Load data ----------
master = load_master()

# ---------- Header ----------
st.title("AfriQuant")
st.caption("Malawian Macroeconomic Data Intelligence Platform")

st.warning(
    "Showing placeholder data (not real economic figures) until real "
    "data replaces the sample files in data/raw/.",
    icon="⚠️",
)

# ---------- Section 1: Snapshot of all 8 indicators ----------
st.subheader("Latest Snapshot")

snapshot = latest_snapshot(master)

cols = st.columns(4)
for i, row in enumerate(snapshot.itertuples()):
    col = cols[i % 4]
    change_text = (
        f"{row.mom_change:+.2f}% MoM" if pd.notna(row.mom_change) else "—"
    )
    col.metric(
        label=f"{row.indicator_name} ({row.unit})",
        value=f"{row.value:,.2f}",
        delta=change_text,
    )

st.divider()

# ---------- Section 2: Drill into one indicator ----------
st.subheader("Indicator History")

indicator_names = sorted(master["indicator_name"].unique())
choice = st.selectbox("Choose an indicator", indicator_names)

detail = master[master["indicator_name"] == choice].sort_values("date")

left, right = st.columns([2, 1])

with left:
    st.line_chart(detail.set_index("date")[["value", "rolling_3m_avg"]])

with right:
    st.write(f"**Unit:** {detail['unit'].iloc[0]}")
    st.write(f"**Latest value:** {detail['value'].iloc[-1]:,.2f}")
    st.write(f"**Data points:** {len(detail)}")

with st.expander("See raw data for this indicator"):
    st.dataframe(detail[["date", "value", "mom_change", "yoy_change", "rolling_3m_avg"]])