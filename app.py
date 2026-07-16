"""
app.py
------
AfriQuant Phase 4: dashboard reading from SQLite (data/output/afriquant.db).
Produced by pipeline.py -> database.py. This file only reads and displays.

Run this from the project's root folder:
    streamlit run app.py
"""

import pandas as pd
import sqlite3
import streamlit as st
import os

DB_FILE = "data/output/afriquant.db"

st.set_page_config(page_title="AfriQuant", layout="wide")


@st.cache_data
def load_master() -> pd.DataFrame:
    if not os.path.exists(DB_FILE):
        st.error(
            f"Can't find {DB_FILE}. Run `python pipeline.py` then "
            f"`python database.py` first."
        )
        st.stop()
    conn = sqlite3.connect(DB_FILE)
    query = """
        SELECT o.date, o.indicator, i.indicator_name, i.unit,
               o.value, o.mom_change, o.yoy_change, o.rolling_3m_avg
        FROM observations o
        JOIN indicators i ON o.indicator = i.indicator
    """
    df = pd.read_sql_query(query, conn, parse_dates=["date"])
    conn.close()
    return df


def latest_snapshot(df: pd.DataFrame) -> pd.DataFrame:
    latest = df.sort_values("date").groupby("indicator").tail(1)
    return latest[["indicator_name", "unit", "date", "value", "mom_change"]]


master = load_master()

st.markdown(
    """
    <div style="
        background: linear-gradient(90deg, #E8720C 0%, #F4A83D 100%);
        padding: 28px 32px;
        border-radius: 10px;
        margin-bottom: 24px;
    ">
        <h1 style="color: white; margin: 0; font-size: 2.3rem;">🌍 AfriQuant</h1>
        <p style="color: #FDF1E6; margin: 4px 0 0 0; font-size: 1.05rem;">
            Malawian Macroeconomic Data Intelligence Platform
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Latest Snapshot")
snapshot = latest_snapshot(master)
cols = st.columns(4)
for i, row in enumerate(snapshot.itertuples()):
    col = cols[i % 4]
    change_text = f"{row.mom_change:+.2f}% MoM" if pd.notna(row.mom_change) else "—"
    col.metric(label=f"{row.indicator_name} ({row.unit})", value=f"{row.value:,.2f}", delta=change_text)

st.divider()

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