from flask import Flask, jsonify, request

from db_repository import repository
from user_api.serializers import (
    serialize_report_response,
    serialize_category_response,
    serialize_status_response,
    serialize_create_report_request_data,
    serialize_update_report_request_data,
    serialize_get_reports_query_params,
)

app = Flask(__name__)
app.json.sort_keys = False


@app.route("/api/v1/healthcheck", methods=["GET"])
def healthcheck():
    return jsonify(status="ok"), 200


@app.route("/api/v1/categories", methods=["GET"])
def get_categories():
    categories = repository.get_categories()
    return jsonify([serialize_category_response(category) for category in categories])


@app.route("/api/v1/statuses", methods=["GET"])
def get_statuses():
    statuses = repository.get_statuses()
    return jsonify([serialize_status_response(status) for status in statuses])


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

    return jsonify({"ticketId": report["ticket_id"]}), 201


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
    try:
        validated_params = serialize_get_reports_query_params(query_params)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    reports = repository.get_reports(validated_params)
    return jsonify([serialize_report_response(report) for report in reports])
