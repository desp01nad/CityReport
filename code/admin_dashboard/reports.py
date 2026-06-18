import streamlit as st

from utils import (
    get_statuses,
    get_category_names,
    fetch_reports,
    load_thumbnail,
    format_datetime,
)
from map import (
    build_js_map_html,
    MAP_SIZE,
    INITIAL_CENTER,
    INITIAL_ZOOM,
    SELECTED_ZOOM,
)
from weather import WMO_DESCRIPTIONS, fetch_weather
from db_repository import repository
import pandas as pd

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
    "quality",
    "priority",
]

QUALITY_OPTIONS = ["low", "normal", "high"]
PRIORITY_OPTIONS = ["low", "medium", "high", "urgent"]


def _render_detail_panel(report: pd.Series):
    st.subheader(f"#{report['ticket_id']} - {report['title']}")
    info_col, weather_col = st.columns(2)

    with info_col:
        st.markdown(f"**Category:** {report['category_name']}")
        st.markdown(f"**Quality:** {report['quality']}")
        st.markdown(f"**Priority:** {report['priority']}")
        st.markdown(
            f"**Coordinates:** {report['latitude']:.4f}, {report['longitude']:.4f}"
        )
        st.markdown(f"**Reported:** {format_datetime(report['created_at'])}")
        st.markdown(f"**Updated:** {format_datetime(report['updated_at'])}")
        st.markdown(f"**Resolved:** {format_datetime(report['resolved_at'])}")

    with weather_col:
        st.markdown("**Current Weather**")
        weather = fetch_weather(report["latitude"], report["longitude"])
        if weather:
            current = weather["current"]
            desc = WMO_DESCRIPTIONS.get(current["weather_code"], "Unknown")
            st.markdown(f"**{desc}**")
            st.markdown(
                f"Temperature: {current['temperature_2m']:.1f}°C "
                f"(feels like {current['apparent_temperature']:.1f}°C)"
            )
            st.markdown(f"Humidity: {current['relative_humidity_2m']}%")
            st.markdown(f"Wind: {current['wind_speed_10m']:.1f} km/h")
        else:
            st.warning("Could not fetch weather data.")

    if report.get("description"):
        st.markdown(f"**Description:** {report['description']}")

    if isinstance(report.get("image_path"), str):
        thumbnail = load_thumbnail(report["image_path"])
        if thumbnail:
            st.image(thumbnail)

    st.divider()

    status_list = get_statuses()
    status_names = [s["status_name"] for s in status_list]
    current_idx = status_names.index(report["status_name"])

    new_status = st.selectbox(
        "Status",
        status_names,
        index=current_idx,
        key=f"status_{report['ticket_id']}",
    )
    new_comments = st.text_area(
        "Admin Comments",
        value=report["admin_comments"] or "",
        key=f"comments_{report['ticket_id']}",
    )

    _, btn_col = st.columns([3, 1])
    if btn_col.button(
        "Save Changes",
        type="primary",
        key=f"save_{report['ticket_id']}",
        use_container_width=True,
    ):
        status_id = next(
            s["status_id"] for s in status_list if s["status_name"] == new_status
        )
        result = repository.admin_update_report(
            ticket_id=report["ticket_id"],
            status_id=status_id,
            admin_comments=new_comments or None,
            is_resolved=(new_status == "Resolved"),
        )
        if result:
            st.toast("Report updated successfully!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Update failed — report not found.")


top_row = st.container()
bottom_row = st.container()

# Fetch and prepare data
_FILTER_KEYS = (
    "filter_category",
    "filter_status",
    "filter_quality",
    "filter_priority",
    "filter_title",
    "filter_description",
    "filter_created_after",
    "filter_created_before",
    "filter_updated_after",
    "filter_updated_before",
    "filter_resolved_after",
    "filter_resolved_before",
)

selected_report_id = st.session_state.get("selected_report_id")

filter_signature = tuple(st.session_state.get(k) or None for k in _FILTER_KEYS)
if st.session_state.get("_prev_filter_signature", filter_signature) != filter_signature:
    selected_report_id = None
    st.session_state.selected_report_id = None
st.session_state._prev_filter_signature = filter_signature

reports = fetch_reports(
    order_by="created_at",
    order="desc",
    category=st.session_state.get("filter_category") or None,
    status=st.session_state.get("filter_status") or None,
    quality=st.session_state.get("filter_quality") or None,
    priority=st.session_state.get("filter_priority") or None,
    title=st.session_state.get("filter_title") or None,
    description=st.session_state.get("filter_description") or None,
    created_after=st.session_state.get("filter_created_after"),
    created_before=st.session_state.get("filter_created_before"),
    updated_after=st.session_state.get("filter_updated_after"),
    updated_before=st.session_state.get("filter_updated_before"),
    resolved_after=st.session_state.get("filter_resolved_after"),
    resolved_before=st.session_state.get("filter_resolved_before"),
)
df = pd.DataFrame(reports, columns=REPORT_COLUMNS)
df["thumbnail"] = df["image_path"].apply(
    lambda p: load_thumbnail(p) if isinstance(p, str) else None
)
match = df[df["ticket_id"] == selected_report_id]
selected_report_row = match.iloc[0] if not match.empty else None

if selected_report_row is None and selected_report_id is not None:
    selected_report_id = None
    st.session_state.selected_report_id = None

with top_row:
    left_col, right_col = st.columns([1, 4])
    with left_col:
        start = st.session_state.setdefault(
            "map_view", {"center": INITIAL_CENTER, "zoom": INITIAL_ZOOM}
        )
        if selected_report_row is not None:
            selected_id = int(selected_report_row["ticket_id"])
            target = {
                "center": [
                    float(selected_report_row["latitude"]),
                    float(selected_report_row["longitude"]),
                ],
                "zoom": SELECTED_ZOOM,
            }
        else:
            selected_id = None
            target = {"center": INITIAL_CENTER, "zoom": INITIAL_ZOOM}

        st.components.v1.html(
            build_js_map_html(reports, selected_id, start, target, height=MAP_SIZE),
            height=MAP_SIZE,
            width=int(2 * MAP_SIZE),
        )
        st.session_state.map_view = target

    with right_col:
        f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)
        with f_col1:
            st.selectbox(
                "Category",
                options=[""] + get_category_names(),
                key="filter_category",
            )
        with f_col2:
            st.selectbox(
                "Status",
                options=[""] + [s["status_name"] for s in get_statuses()],
                key="filter_status",
            )
        with f_col3:
            st.selectbox(
                "Quality",
                options=[""] + QUALITY_OPTIONS,
                key="filter_quality",
            )
        with f_col4:
            st.selectbox(
                "Priority",
                options=[""] + PRIORITY_OPTIONS,
                key="filter_priority",
            )
        with f_col5:
            st.text_input("Title", key="filter_title")
        with f_col6:
            st.text_input("Description", key="filter_description")

        d_col1, d_col2, d_col3, d_col4, d_col5, d_col6 = st.columns(6)
        with d_col1:
            st.date_input("Reported after", value=None, key="filter_created_after")
        with d_col2:
            st.date_input("Reported before", value=None, key="filter_created_before")
        with d_col3:
            st.date_input("Updated after", value=None, key="filter_updated_after")
        with d_col4:
            st.date_input("Updated before", value=None, key="filter_updated_before")
        with d_col5:
            st.date_input("Resolved after", value=None, key="filter_resolved_after")
        with d_col6:
            st.date_input("Resolved before", value=None, key="filter_resolved_before")

with bottom_row:
    if selected_report_row is not None:
        table_col, detail_col = st.columns([3, 2])
    else:
        table_col = st.columns([1])[0]
        detail_col = None

    with table_col:
        st.subheader(f"Reports ({len(reports)})")
        if df.empty:
            st.info("No reports match the current filters.")
        else:
            df_row_height_px = 35
            event = st.dataframe(
                df[
                    [
                        "ticket_id",
                        "thumbnail",
                        "title",
                        "description",
                        "category_name",
                        "status_name",
                        "quality",
                        "priority",
                        "latitude",
                        "longitude",
                        "created_at",
                        "updated_at",
                        "resolved_at",
                        "admin_comments",
                    ]
                ],
                column_config={
                    "ticket_id": st.column_config.NumberColumn("ID"),
                    "thumbnail": st.column_config.ImageColumn("Image", width="small"),
                    "title": st.column_config.TextColumn("Title", width="medium"),
                    "description": st.column_config.TextColumn(
                        "Description", width="large"
                    ),
                    "category_name": st.column_config.TextColumn("Category"),
                    "status_name": st.column_config.TextColumn("Status"),
                    "quality": st.column_config.TextColumn("Quality"),
                    "priority": st.column_config.TextColumn("Priority"),
                    "latitude": st.column_config.NumberColumn("Lat", format="%.4f"),
                    "longitude": st.column_config.NumberColumn("Lon", format="%.4f"),
                    "created_at": st.column_config.DatetimeColumn(
                        "Reported", format="DD/MM/YY HH:mm"
                    ),
                    "updated_at": st.column_config.DatetimeColumn(
                        "Updated", format="DD/MM/YY HH:mm"
                    ),
                    "resolved_at": st.column_config.DatetimeColumn(
                        "Resolved", format="DD/MM/YY HH:mm"
                    ),
                    "admin_comments": st.column_config.TextColumn(
                        "Admin Comments", width="large"
                    ),
                },
                width="stretch",
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                row_height=df_row_height_px,
                height=df_row_height_px * 20,
                key=f"reports_df_{hash(filter_signature)}",
            )
            selected_rows = event.selection.rows
            if selected_rows:
                new_id = int(df.iloc[selected_rows[0]]["ticket_id"])
            else:
                new_id = None
            if new_id != selected_report_id:
                st.session_state.selected_report_id = new_id
                st.rerun()

    if detail_col:
        with detail_col:
            _render_detail_panel(selected_report_row)
