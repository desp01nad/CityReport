from flask import Flask, jsonify, request
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from db_repository import repository
from user_api.serializers import (
    serialize_create_report_request_data,
    serialize_update_report_request_data,
)

app = Flask(__name__)
app.json.sort_keys = False


@app.route("/api/v1/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify(status="ok"), 200


@app.route("/api/v1/categories", methods=["GET"])
def get_categories():
    return repository.get_categories()


@app.route("/api/v1/statuses", methods=["GET"])
def get_statuses():
    return repository.get_statuses()


@app.route("/api/v1/reports", methods=["POST"])
def create_report():
    data = request.get_json(silent=True)
    try:
        validated_data = serialize_create_report_request_data(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    report = repository.create_report(
        validated_data["title"],
        validated_data["description"],
        validated_data["category_id"],
        validated_data["status_id"],
        validated_data["latitude"],
        validated_data["longitude"],
    )
    if report is None:
        return jsonify({"error": "Report not created"}), 500

    return jsonify(report), 201


@app.route("/api/v1/report/<int:ticket_id>", methods=["GET"])
def get_report(ticket_id):
    report = repository.get_report(ticket_id)
    if report is None:
        return jsonify({"error": "Report not found"}), 404

    return jsonify(report)


@app.route("/api/v1/report/<int:ticket_id>", methods=["PATCH"])
def update_report(ticket_id):
    data = request.get_json(silent=True)
    try:
        validated_data = serialize_update_report_request_data(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    report = repository.update_report(ticket_id, validated_data)
    if report is None:
        return jsonify({"error": "Report not found"}), 404

    return jsonify(report)


@app.route("/api/v1/reports", methods=["GET"])
def get_reports():
    query_params = request.args

    order = query_params.get("order", "").lower()
    if order not in ["asc", "desc"]:
        raise ValueError(f"Order field should be asc or desc")
    order = sql.SQL("ASC") if order == "asc" else sql.SQL("DESC")
    order_by = query_params.get("order_by", "").lower()
    ordering_fields = (
        "createdat",
        "updatedat",
        "resolvedat",
        "title",
        "category",
        "status",
    )
    if not order_by:
        order_by = "createdAt"
    elif order_by not in ordering_fields:
        raise ValueError(f"Order by field should be one of {ordering_fields}")

    ordering_mapping = {
        "title": sql.SQL("CR.Title"),
        "createdat": sql.SQL("CR.createdAt"),
        "updatedat": sql.SQL("CR.updatedAt"),
        "resolvedat": sql.SQL("CR.resolvedAt"),
        "status": sql.SQL("S.statusname"),
        "category": sql.SQL("C.categoryname"),
    }
    order_by = ordering_mapping[order_by]
    sql_query = sql.SQL("""
        SELECT TicketId, Title, Description, C.categoryname, S.statusname, Latitude, Longitude, ImagePath, CreatedAt, UpdatedAt, ResolvedAt 
        FROM CityReports CR
        JOIN Categories C ON CR.CategoryId = C.CategoryId
        JOIN Statuses S ON CR.StatusId = S.StatusId 
        ORDER BY {} {}
    """).format(order_by, order)
    print(sql_query)

    with psycopg.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql_query)
            reports = cur.fetchall()

    return reports
