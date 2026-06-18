import pandas as pd
import plotly.express as px
import streamlit as st

from utils import fetch_reports

REPORT_COLUMNS = [
    "ticket_id",
    "title",
    "description",
    "category_name",
    "status_name",
    "latitude",
    "longitude",
    "image_path",
    "created_at",
    "updated_at",
    "resolved_at",
    "admin_comments",
]

OPEN_STATUSES = ("Reported", "In Progress")

st.title("Analysis")

reports = fetch_reports(order_by="created_at", order="desc")
df = pd.DataFrame(reports, columns=REPORT_COLUMNS)

if df.empty:
    st.info("No reports yet.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
df["resolved_at"] = pd.to_datetime(df["resolved_at"], utc=True)
df["resolution_days"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 86400

now = pd.Timestamp.now(tz="UTC")
new_last_7d = int((df["created_at"] >= now - pd.Timedelta(days=7)).sum())
resolved = df[df["status_name"] == "Resolved"]
median_resolution = df["resolution_days"].median()

total_col, open_col, rate_col, time_col = st.columns(4)
total_col.metric("Total Reports", len(df), delta=f"{new_last_7d} this week")
open_col.metric("Open Reports", int(df["status_name"].isin(OPEN_STATUSES).sum()))
rate_col.metric("Resolution Rate", f"{len(resolved) / len(df):.0%}")
time_col.metric(
    "Median Resolution Time",
    f"{median_resolution:.1f} d" if pd.notna(median_resolution) else "—",
)

st.divider()

trend_col, category_col = st.columns(2)

with trend_col:
    weekly = (
        df.set_index("created_at")
        .resample("W")
        .size()
        .rename("count")
        .reset_index()
    )
    fig = px.area(
        weekly,
        x="created_at",
        y="count",
        title="Reports Over Time (weekly)",
        labels={"created_at": "Week", "count": "New reports"},
    )
    st.plotly_chart(fig, use_container_width=True)

with category_col:
    by_category = (
        df["category_name"].value_counts().sort_values().rename("count").reset_index()
    )
    fig = px.bar(
        by_category,
        x="count",
        y="category_name",
        orientation="h",
        title="Reports by Category",
        labels={"category_name": "Category", "count": "Reports"},
    )
    st.plotly_chart(fig, use_container_width=True)

status_col, restime_col = st.columns(2)

with status_col:
    by_status = df["status_name"].value_counts().rename("count").reset_index()
    fig = px.pie(
        by_status,
        names="status_name",
        values="count",
        hole=0.5,
        title="Status Breakdown",
    )
    st.plotly_chart(fig, use_container_width=True)

with restime_col:
    if resolved.empty:
        st.info("No resolved reports yet.")
    else:
        fig = px.box(
            resolved,
            x="category_name",
            y="resolution_days",
            title="Resolution Time by Category",
            labels={"category_name": "Category", "resolution_days": "Days to resolve"},
        )
        st.plotly_chart(fig, use_container_width=True)
