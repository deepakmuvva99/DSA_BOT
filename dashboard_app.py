import os
from io import BytesIO

import pandas as pd
import requests
import streamlit as st


st.set_page_config(page_title="DSA Progress Dashboard", layout="wide")


def load_tracker():
    tracker_url = st.sidebar.text_input("Tracker URL (optional)", value=os.getenv("TRACKER_XLSX_URL", ""))
    local_file = st.sidebar.text_input("Local tracker path", value="DSA_Master_Tracker.xlsx")

    if tracker_url.strip():
        if "docs.google.com/spreadsheets/d/" in tracker_url and "/export?" not in tracker_url:
            sheet_id = tracker_url.split("/spreadsheets/d/", 1)[1].split("/", 1)[0]
            tracker_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
        response = requests.get(tracker_url, timeout=30)
        response.raise_for_status()
        return pd.read_excel(BytesIO(response.content), sheet_name=None)

    return pd.read_excel(local_file, sheet_name=None)


def main():
    st.title("AI Coach Progress Dashboard")
    sheets = load_tracker()
    dsa = sheets["DSA Problems"].copy()

    if "Confidence (1-5)" not in dsa.columns:
        dsa["Confidence (1-5)"] = 3

    completed = dsa[dsa["Status"] == "Completed"].copy()
    completed["First Attempt Date"] = pd.to_datetime(completed["First Attempt Date"], errors="coerce")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total DSA Problems", len(dsa))
    col2.metric("Completed", len(completed))
    col3.metric("Avg Accuracy", f"{completed['Accuracy (%)'].mean():.1f}%" if len(completed) else "0.0%")
    col4.metric("Avg Confidence", f"{completed['Confidence (1-5)'].mean():.2f}/5" if len(completed) else "0.00/5")

    st.subheader("Pattern Heatmap (Accuracy %)")
    heat = completed.pivot_table(index="Pattern", columns="Difficulty", values="Accuracy (%)", aggfunc="mean")
    st.dataframe(heat.style.background_gradient(cmap="RdYlGn"))

    st.subheader("Rolling Accuracy (last 20 solved)")
    timeline = completed.dropna(subset=["First Attempt Date"]).sort_values("First Attempt Date")
    timeline["rolling_accuracy"] = timeline["Accuracy (%)"].rolling(20, min_periods=1).mean()
    st.line_chart(timeline.set_index("First Attempt Date")["rolling_accuracy"])

    st.subheader("Completion Velocity (weekly)")
    timeline["week"] = timeline["First Attempt Date"].dt.to_period("W").astype(str)
    weekly = timeline.groupby("week")["Problem Name"].count().rename("Solved Count")
    st.bar_chart(weekly)

    st.subheader("Low Confidence Queue")
    low_conf = completed[completed["Confidence (1-5)"] <= 2][
        ["Problem Name", "Pattern", "Difficulty", "Accuracy (%)", "Confidence (1-5)", "LeetCode Link"]
    ]
    st.dataframe(low_conf.head(50))


if __name__ == "__main__":
    main()
