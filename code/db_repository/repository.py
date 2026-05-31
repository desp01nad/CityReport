from datetime import datetime
from typing import TypedDict

import psycopg
from psycopg.rows import dict_row


class Report(TypedDict):
    ticket_id: int
    title: str
    description: str | None
    category_name: str
    status_name: str
    latitude: float
    longitude: float
    image_path: str | None
    created_at: datetime
    updated_at: datetime | None
    resolved_at: datetime | None
    admin_comments: str | None


def connect():
    return psycopg.connect(options="-c timezone=UTC")


def get_categories() -> list[dict[str, int | str]]:
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT category_id, category_name
                FROM categories
                """)
            return cur.fetchall()


def get_statuses() -> list[dict[str, int | str]]:
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT status_id, status_name
                FROM statuses
                """)
            return cur.fetchall()


def get_report(ticket_id: int) -> Report | None:
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT cr.ticket_id, cr.title, cr.description,
                       c.category_name, s.status_name,
                       cr.latitude::float8 AS latitude,
                       cr.longitude::float8 AS longitude,
                       cr.image_path, cr.created_at, cr.updated_at,
                       cr.resolved_at, cr.admin_comments
                FROM city_reports cr
                JOIN categories c ON cr.category_id = c.category_id
                JOIN statuses s ON cr.status_id = s.status_id
                WHERE cr.ticket_id = %s
                """,
                (ticket_id,),
            )
            return cur.fetchone()


def get_reports(filter_order_params):
    base_query = """
        SELECT cr.ticket_id, cr.title, cr.description,
               c.category_name, s.status_name,
               cr.latitude::float8 AS latitude,
               cr.longitude::float8 AS longitude,
               cr.image_path, cr.created_at, cr.updated_at, cr.resolved_at
        FROM city_reports cr
        JOIN categories c ON cr.category_id = c.category_id
        JOIN statuses s ON cr.status_id = s.status_id
    """

    order = filter_order_params.pop("order", "")
    order = "ASC" if order == "asc" else "DESC"
    order_by = filter_order_params.pop("order_by", None)
    ordering_mapping = {
        "title": "cr.title",
        "status": "s.status_name",
        "category": "c.category_name",
        "created_at": "cr.created_at",
        "updated_at": "cr.updated_at",
        "resolved_at": "cr.resolved_at",
    }
    order_by = (
        ordering_mapping[order_by] if order_by else ordering_mapping["created_at"]
    )
    ordering_query = f" ORDER BY {order_by} {order}"

    filter_queries = set()
    filtering_mapping = {
        "category": "c.category_name = '{value}'",
        "status": "s.status_name = '{value}'",
        "title": "cr.title ILIKE '%{value}%'",
        "description": "cr.description ILIKE '%{value}%'",
        "created_before": "cr.created_at < '{value}'",
        "created_after": "cr.created_at > '{value}'",
        "updated_before": "cr.updated_at < '{value}'",
        "updated_after": "cr.updated_at > '{value}'",
        "resolved_before": "cr.resolved_at < '{value}'",
        "resolved_after": "cr.resolved_at > '{value}'",
    }
    for query_filter, value in filter_order_params.items():
        filter_queries.add(filtering_mapping[query_filter].format(value=value))
    filtering_query = " WHERE " + " AND ".join(filter_queries) if filter_queries else ""

    query = base_query + filtering_query + ordering_query

    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query)
            return cur.fetchall()


def create_report(
    title, description, category_id, status_id, latitude, longitude, image_path
) -> dict[str, int] | None:
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO city_reports (
                    title, description, category_id, status_id, latitude, longitude, image_path
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING ticket_id;
                """,
                (
                    title,
                    description,
                    category_id,
                    status_id,
                    latitude,
                    longitude,
                    image_path,
                ),
            )
            return cur.fetchone()


def update_report(
    ticket_id: int, updates: dict[str, object], image_path
) -> Report | None:
    if not updates:
        raise ValueError("At least one field is required")

    set_clauses = [f"{field} = %s" for field in updates]
    values = [updates[field] for field in updates]
    if image_path:
        set_clauses.append(f"image_path = %s")
        values.append(image_path)
    set_clauses.append("updated_at = CURRENT_TIMESTAMP")
    values.append(ticket_id)

    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                f"""
                WITH updated AS (
                    UPDATE city_reports
                    SET {", ".join(set_clauses)}
                    WHERE ticket_id = %s
                    RETURNING *
                )
                SELECT updated.ticket_id, updated.title, updated.description,
                       c.category_name, s.status_name,
                       updated.latitude::float8 AS latitude,
                       updated.longitude::float8 AS longitude,
                       updated.image_path,
                       updated.created_at, updated.updated_at, updated.resolved_at,
                       updated.admin_comments
                FROM updated
                JOIN categories c ON updated.category_id = c.category_id
                JOIN statuses s ON updated.status_id = s.status_id
                """,
                values,
            )
            return cur.fetchone()
