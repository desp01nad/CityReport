from datetime import datetime
from typing import TypedDict, cast

import psycopg
from psycopg.rows import dict_row


class Report(TypedDict):
    ticketid: int
    title: str
    description: str | None
    categoryname: str
    statusname: str
    latitude: float
    longitude: float
    imagepath: str | None
    createdat: datetime
    updatedat: datetime | None
    resolvedat: datetime | None


def get_categories() -> list[dict[str, int | str]]:
    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT CategoryId, CategoryName
                FROM Categories
                """)
            return cur.fetchall()


def get_statuses() -> list[dict[str, int | str]]:
    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT StatusId, StatusName
                FROM Statuses
                """)
            return cur.fetchall()


def get_report(ticket_id: int) -> Report | None:
    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT TicketId, Title, Description, C.categoryname, S.statusname, Latitude, Longitude, ImagePath, CreatedAt, UpdatedAt, ResolvedAt
                FROM CityReports CR
                JOIN Categories C ON CR.CategoryId = C.CategoryId
                JOIN Statuses S ON CR.StatusId = S.StatusId
                WHERE CR.TicketId = %s
                """,
                (ticket_id,),
            )
            return cur.fetchone()


def create_report(
    title, description, category_id, status_id, latitude, longitude
) -> dict[str, int]:
    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO CityReports (Title, Description, CategoryId, StatusId, Latitude, Longitude)
                VALUES (%s, %s, %s,%s, %s, %s)
                RETURNING TicketId;
                """,
                (
                    title,
                    description,
                    category_id,
                    status_id,
                    latitude,
                    longitude,
                ),
            )
            return cur.fetchone()
