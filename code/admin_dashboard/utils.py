import base64
import os

import pandas as pd
import streamlit as st

from db_repository import repository

REPORT_IMAGES_DIR = os.getenv("REPORT_IMAGES_DIR", "/mnt/report-images")


@st.cache_data(ttl=30)
def get_statuses():
    return repository.get_statuses()


@st.cache_data(ttl=30)
def get_category_names():
    return [c["category_name"] for c in repository.get_categories()]


@st.cache_data(ttl=60)
def fetch_reports(
    order_by,
    order,
    category=None,
    status=None,
    title=None,
    description=None,
    created_after=None,
    created_before=None,
    updated_after=None,
    updated_before=None,
    resolved_after=None,
    resolved_before=None,
    quality=None,
    priority=None,
):
    params = {"order_by": order_by, "order": order}
    if category:
        params["category"] = category
    if status:
        params["status"] = status
    if quality:
        params["quality"] = quality
    if priority:
        params["priority"] = priority
    if title:
        params["title"] = title
    if description:
        params["description"] = description
    if created_after:
        params["created_after"] = created_after
    if created_before:
        params["created_before"] = created_before
    if updated_after:
        params["updated_after"] = updated_after
    if updated_before:
        params["updated_before"] = updated_before
    if resolved_after:
        params["resolved_after"] = resolved_after
    if resolved_before:
        params["resolved_before"] = resolved_before
    return repository.get_reports(params)


@st.cache_data(ttl=300)
def load_thumbnail(image_path):
    full_path = os.path.join(REPORT_IMAGES_DIR, image_path)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        raw = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(image_path)[1].lstrip(".").lower()
    mime = "jpeg" if ext == "jpg" else ext
    return f"data:image/{mime};base64,{raw}"


def format_datetime(dt):
    if dt is None or pd.isna(dt):
        return "-"
    return dt.strftime("%d/%m/%Y %H:%M")
