from flask import Flask, jsonify, request
import psycopg
from psycopg.rows import dict_row
from db_repository import repository
from user_api.serializers import serialize_create_report_request_data

app = Flask(__name__)


@app.route("/api/v1/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify(status="ok"), 200


@app.route("/api/v1/categories", methods=["GET"])
def get_categories():
    return repository.get_categories()


@app.route("/api/v1/statuses", methods=["GET"])
def get_statuses():
    return repository.get_statuses()


@app.route("/api/v1/reports", methods=["GET"])
def get_reports():
    # TODO: Refactor and support filtering and ordering
    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT TicketId, Title, Description, Latitude, Longitude, ImagePath, CreatedAt, UpdatedAt, ResolvedAt, C.categoryname  , S.statusname
                FROM CityReports CR
                JOIN Categories C ON CR.CategoryId = C.CategoryId
                JOIN Statuses S ON CR.StatusId = S.StatusId
                ORDER BY CreatedAt DESC
                """)
            reports = cur.fetchall()

    return reports


@app.route("/api/v1/reports", methods=["POST"])
def create_report():
    data = request.json
    validated_data = serialize_create_report_request_data(data)
    row = repository.create_report(
        validated_data["title"],
        validated_data["description"],
        validated_data["category_id"],
        validated_data["status_id"],
        validated_data["latitude"],
        validated_data["longitude"],
    )
    return jsonify(row), 201
