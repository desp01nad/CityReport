import json

from flask import Flask, jsonify, request, send_from_directory

from db_repository import repository
from user_api.genai import assess_report
from user_api.serializers import (
    serialize_report_response,
    serialize_category_response,
    serialize_status_response,
    serialize_create_report_request_data,
    serialize_update_report_request_data,
    serialize_get_reports_query_params,
    validate_and_save_uploaded_image,
)
from user_api.settings import REPORT_IMAGES_DIR

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
    """Create a report from a multipart request and return its ticket ID.

    Expects report fields as JSON under the ``data`` form key and an optional
    ``image`` file. Returns the new ``ticketId`` (201), or an error payload.
    """
    try:
        data = json.loads(request.form["data"])
    except KeyError, json.JSONDecodeError:
        return (
            jsonify(
                {
                    "error": "Report fields should be sent as JSON under the 'data' form key"
                }
            ),
            400,
        )
    image = request.files.get("image")

    try:
        validated_data = serialize_create_report_request_data(data)
        image_path = validate_and_save_uploaded_image(image)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    assessment = assess_report(
        validated_data["title"],
        validated_data["description"],
        data.get("category") or "Generic",
    )

    report = repository.create_report(
        validated_data["title"],
        validated_data["description"],
        validated_data["category_id"],
        validated_data["status_id"],
        validated_data["latitude"],
        validated_data["longitude"],
        image_path,
        assessment["quality"],
        assessment["priority"],
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
    """Apply a citizen update to an existing report and return the updated report.

    Expects changed fields as JSON under the ``data`` form key and an optional new
    ``image`` file. Re-runs the AI assessment and returns the report, or an error.
    """
    try:
        data = json.loads(request.form["data"])
    except KeyError, json.JSONDecodeError:
        return (
            jsonify(
                {
                    "error": "Report fields should be sent as JSON under the 'data' form key"
                }
            ),
            400,
        )
    image = request.files.get("image")

    try:
        validated_data = serialize_update_report_request_data(data)
        image_path = validate_and_save_uploaded_image(image)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    existing = repository.get_report(ticket_id)
    if existing is None:
        return jsonify({"error": "Report not found"}), 404

    assessment = assess_report(
        validated_data.get("title", existing["title"]),
        validated_data.get("description", existing["description"]),
        data.get("category") or existing["category_name"],
    )
    validated_data["quality"] = assessment["quality"]
    validated_data["priority"] = assessment["priority"]

    report = repository.update_report(ticket_id, validated_data, image_path)
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


@app.route("/api/v1/report-images/<int:ticket_id>", methods=["GET"])
def get_report_images(ticket_id):
    report = repository.get_report(ticket_id)
    if report is None:
        return jsonify({"error": "Report not found"}), 404

    image_path = report.get("image_path")
    if image_path is None:
        return jsonify({"error": "Report has no image"}), 404

    return send_from_directory(REPORT_IMAGES_DIR, image_path)
