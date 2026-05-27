import psycopg
from psycopg.rows import dict_row


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
