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
    quality: str
    priority: str


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
                       cr.resolved_at, cr.admin_comments, cr.quality, cr.priority
                FROM city_reports cr
                JOIN categories c ON cr.category_id = c.category_id
                JOIN statuses s ON cr.status_id = s.status_id
                WHERE cr.ticket_id = %s
                """,
                (ticket_id,),
            )
            return cur.fetchone()


def get_reports(filter_order_params):
    """Build and run a dynamic query that filters and orders city reports.

    Args:
        filter_order_params: Dict of filters plus optional ``order`` ("asc"/"desc")
            and ``order_by`` keys, which are consumed while building the query.

    Returns:
        List of matching report rows as dicts.
    """
    base_query = """
        SELECT cr.ticket_id, cr.title, cr.description,
               c.category_name, s.status_name,
               cr.latitude::float8 AS latitude,
               cr.longitude::float8 AS longitude,
               cr.image_path, cr.created_at, cr.updated_at, cr.resolved_at,
               cr.admin_comments, cr.quality, cr.priority
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

    filtering_mapping = {
        "category": "c.category_name = %s",
        "status": "s.status_name = %s",
        "title": "cr.title ILIKE %s",
        "description": "cr.description ILIKE %s",
        "created_before": "cr.created_at < %s",
        "created_after": "cr.created_at > %s",
        "updated_before": "cr.updated_at < %s",
        "updated_after": "cr.updated_at > %s",
        "resolved_before": "cr.resolved_at < %s",
        "resolved_after": "cr.resolved_at > %s",
        "quality": "cr.quality = %s",
        "priority": "cr.priority = %s",
    }
    ilike_filters = {"title", "description"}
    filter_clauses = []
    params = []
    for query_filter, value in filter_order_params.items():
        filter_clauses.append(filtering_mapping[query_filter])
        params.append(f"%{value}%" if query_filter in ilike_filters else value)
    filtering_query = " WHERE " + " AND ".join(filter_clauses) if filter_clauses else ""

    query = base_query + filtering_query + ordering_query

    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def create_report(
    title,
    description,
    category_id,
    status_id,
    latitude,
    longitude,
    image_path,
    quality,
    priority,
) -> dict[str, int] | None:
    """Insert a new report with status 'Reported'.

    Args:
        title, description, category_id, status_id, latitude, longitude, image_path,
        quality, priority

    Returns:
        Dict with the generated ``ticket_id``, or None if the insert returned nothing.
    """
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO city_reports (
                    title, description, category_id, status_id, latitude, longitude,
                    image_path, quality, priority
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                    quality,
                    priority,
                ),
            )
            return cur.fetchone()


UPDATABLE_FIELDS = {
    "title",
    "description",
    "category_id",
    "latitude",
    "longitude",
    "quality",
    "priority",
}


def admin_update_report(
    ticket_id: int, status_id: int, admin_comments: str | None, is_resolved: bool
) -> Report | None:
    """Update a report's status and admin comments from the dashboard.

    ``resolved_at`` is stamped when the report becomes resolved, kept if the status
    is unchanged, and cleared otherwise.

    Args:
        ticket_id: Report to update.
        status_id: New status.
        admin_comments: Admin notes, or None.
        is_resolved: Whether the new status is the resolved state.

    Returns:
        The updated report row, or None if the ticket does not exist.
    """
    with connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                WITH updated AS (
                    UPDATE city_reports
                    SET status_id = %s,
                        admin_comments = %s,
                        updated_at = CURRENT_TIMESTAMP,
                        resolved_at = CASE
                            WHEN %s = status_id THEN resolved_at
                            WHEN %s THEN CURRENT_TIMESTAMP
                            ELSE NULL
                        END
                    WHERE ticket_id = %s
                    RETURNING *
                )
                SELECT updated.ticket_id, updated.title, updated.description,
                       c.category_name, s.status_name,
                       updated.latitude::float8 AS latitude,
                       updated.longitude::float8 AS longitude,
                       updated.image_path,
                       updated.created_at, updated.updated_at, updated.resolved_at,
                       updated.admin_comments, updated.quality, updated.priority
                FROM updated
                JOIN categories c ON updated.category_id = c.category_id
                JOIN statuses s ON updated.status_id = s.status_id
                """,
                (status_id, admin_comments, status_id, is_resolved, ticket_id),
            )
            return cur.fetchone()


def update_report(
    ticket_id: int, updates: dict[str, object], image_path
) -> Report | None:
    """Apply a partial citizen update to a report's editable fields.

    Args:
        ticket_id: Report to update.
        updates: Field/value pairs; keys must be within ``UPDATABLE_FIELDS``.
        image_path: New image filename to set, or falsy to leave the image unchanged.

    Returns:
        The updated report row, or None if the ticket does not exist.

    Raises:
        ValueError: If ``updates`` is empty or contains unsupported fields.
    """
    if not updates:
        raise ValueError("At least one field is required")

    invalid = updates.keys() - UPDATABLE_FIELDS
    if invalid:
        raise ValueError(f"Invalid fields: {invalid}")

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
                       updated.admin_comments, updated.quality, updated.priority
                FROM updated
                JOIN categories c ON updated.category_id = c.category_id
                JOIN statuses s ON updated.status_id = s.status_id
                """,
                values,
            )
            return cur.fetchone()
