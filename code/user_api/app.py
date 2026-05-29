from flask import Flask, jsonify, request
from psycopg.rows import dict_row
from datetime import datetime
from db_repository import repository
from user_api.serializers import (
    serialize_report_response,
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

    return jsonify({"ticketId": report["ticketid"]}), 201


@app.route("/api/v1/report/<int:ticket_id>", methods=["GET"])
def get_report(ticket_id):
    report = repository.get_report(ticket_id)
    if report is None:
        return jsonify({"error": "Report not found"}), 404

    return jsonify(serialize_report_response(report))


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

    return jsonify(serialize_report_response(report))


@app.route("/api/v1/reports", methods=["GET"])
def get_reports():
    query_params = request.args

    order = query_params.get("order", "").lower()
    if order not in ["asc", "desc"]:
        raise ValueError(f"Order field should be asc or desc")
    order = "ASC" if order == "asc" else "DESC"
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
        order_by = "createdat"
    elif order_by not in ordering_fields:
        raise ValueError(f"Order by field should be one of {ordering_fields}")

    ordering_mapping = {
        "title": "CR.Title",
        "createdat": "CR.createdAt",
        "updatedat": "CR.updatedAt",
        "resolvedat": "CR.resolvedAt",
        "status": "S.statusname",
        "category": "C.categoryname",
    }
    order_by = ordering_mapping[order_by]

    sql_query = """
        SELECT TicketId, Title, Description, C.categoryname, S.statusname,
               Latitude::float8 AS Latitude, Longitude::float8 AS Longitude,
               ImagePath, CreatedAt, UpdatedAt, ResolvedAt
        FROM CityReports CR
        JOIN Categories C ON CR.CategoryId = C.CategoryId
        JOIN Statuses S ON CR.StatusId = S.StatusId
    """

    filter_queries = set()

    category = query_params.get("category")
    if category:
        valid_categories = {
            category["categoryname"]: category["categoryid"]
            for category in repository.get_categories()
        }
        if category not in valid_categories:
            raise ValueError(f"Category field should be one of {valid_categories}")
        filter_queries.add(f"C.categoryname = '{category}'")

    status = query_params.get("status")
    if status:
        valid_statuses = {
            status["statusname"]: status["statusid"]
            for status in repository.get_statuses()
        }
        if status not in valid_statuses:
            raise ValueError(f"Status field should be one of {valid_statuses}")
        filter_queries.add(f"S.statusname = '{status}'")

    created_before = query_params.get("createdBefore")
    if created_before:
        try:
            dt = datetime.fromisoformat(created_before.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.createdat < '{created_before}'")

    created_after = query_params.get("createdAfter")
    if created_after:
        try:
            dt = datetime.fromisoformat(created_after.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.createdat > '{created_after}'")

    updated_before = query_params.get("updatedBefore")
    if updated_before:
        try:
            dt = datetime.fromisoformat(updated_before.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.updatedat < '{updated_before}'")

    updated_after = query_params.get("updatedAfter")
    if updated_after:
        try:
            dt = datetime.fromisoformat(updated_after.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.updatedat > '{updated_after}'")

    resolved_before = query_params.get("resolvedBefore")
    if resolved_before:
        try:
            dt = datetime.fromisoformat(resolved_before.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.resolvedat < '{resolved_before}'")

    resolved_after = query_params.get("resolvedAfter")
    if resolved_after:
        try:
            dt = datetime.fromisoformat(resolved_after.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("Datetime query parameter must be a valid ISO datetime")
        if dt.tzinfo is None:
            raise ValueError("Datetime query parameter must include timezone info")
        filter_queries.add(f"CR.resolvedat > '{resolved_after}'")

    if filter_queries:
        sql_query += " WHERE " + " AND ".join(filter_queries)
    sql_query += f" ORDER BY {order_by} {order}"

    print(sql_query)

    with repository.connect() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql_query)
            reports = cur.fetchall()

    return jsonify([serialize_report_response(report) for report in reports])
