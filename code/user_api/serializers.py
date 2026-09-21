import os
import uuid
from datetime import UTC, datetime

from db_repository import repository
from user_api.settings import API_BASE_URL, ALLOWED_IMAGE_EXTENSIONS, REPORT_IMAGES_DIR


def serialize_create_report_request_data(data):
    """Validate an incoming report payload and resolve it to DB column values.

    Args:
        data: Parsed JSON body of a create-report request.

    Returns:
        Dict of validated fields including resolved ``category_id`` and default
        ``status_id``.

    Raises:
        ValueError: If a required field is missing or any field is invalid.
    """
    # validate mandatory fields
    title = data.get("title")
    if not isinstance(title, str) or len(title) < 1:
        raise ValueError("Field 'title' (str) is required")

    latitude = data.get("latitude")
    longitude = data.get("longitude")
    if any(not isinstance(value, float) for value in (latitude, longitude)):
        raise ValueError("Fields 'longitude' and 'latitude' (float) are required")

    # validate optional fields
    description = data.get("description")
    if description and not isinstance(description, str):
        raise ValueError("Optional field 'description' must be a string")

    category = data.get("category")
    valid_categories = {
        category["category_name"]: category["category_id"]
        for category in repository.get_categories()
    }
    if not category:
        category = "Generic"
    elif category and category not in valid_categories:
        raise ValueError(
            f"Optional field 'category' must be one of {sorted(valid_categories)}"
        )
    category_id = valid_categories[category]
    status_id = 1  # Default status is 'Reported'

    return {
        "title": title,
        "description": description,
        "category_id": category_id,
        "status_id": status_id,
        "latitude": latitude,
        "longitude": longitude,
    }


def serialize_update_report_request_data(data):
    """Validate a partial report-update payload, keeping only supplied fields.

    Args:
        data: Parsed JSON body of an update-report request.

    Returns:
        Dict of validated fields to update (e.g. with resolved ``category_id``).

    Raises:
        ValueError: If the body is not an object, is empty, or a field is invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object")

    if not data:
        raise ValueError("At least one field is required")

    validated_data = {}

    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or len(title) < 1:
            raise ValueError("Field 'title' must be string")
        validated_data["title"] = title

    if "description" in data:
        description = data["description"]
        if description and not isinstance(description, str):
            raise ValueError("Field 'description' must be a string")
        validated_data["description"] = description

    if "category" in data:
        valid_categories = {
            category["category_name"]: category["category_id"]
            for category in repository.get_categories()
        }
        category = data["category"]
        if category not in valid_categories:
            raise ValueError(
                f"Field 'category' must be one of {sorted(valid_categories)}"
            )
        validated_data["category_id"] = valid_categories[category]

    if "latitude" in data:
        latitude = data["latitude"]
        if not isinstance(latitude, float):
            raise ValueError("Field 'latitude' must be a float")
        validated_data["latitude"] = latitude

    if "longitude" in data:
        longitude = data["longitude"]
        if not isinstance(longitude, float):
            raise ValueError("Field 'longitude' must be a float")
        validated_data["longitude"] = longitude

    return validated_data


def serialize_category_response(category):
    return {
        "categoryId": category["category_id"],
        "categoryName": category["category_name"],
    }


def serialize_status_response(status):
    return {
        "statusId": status["status_id"],
        "statusName": status["status_name"],
    }


def serialize_report_response(report):
    return {
        "ticketId": report["ticket_id"],
        "title": report["title"],
        "description": report["description"],
        "categoryName": report["category_name"],
        "statusName": report["status_name"],
        "latitude": report["latitude"],
        "longitude": report["longitude"],
        "imageUrl": (
            f"{API_BASE_URL}/api/v1/report-images/{report["ticket_id"]}"
            if report["image_path"]
            else None
        ),
        "createdAt": serialize_datetime(report["created_at"]),
        "updatedAt": serialize_datetime(report["updated_at"]),
        "resolvedAt": serialize_datetime(report["resolved_at"]),
    }


def serialize_datetime(value):
    """Render a datetime as a UTC ISO-8601 string using a trailing 'Z'.

    Args:
        value: A datetime (naive values are assumed UTC), or None.

    Returns:
        The ISO-8601 string, or None if ``value`` is None.

    Raises:
        ValueError: If ``value`` is neither a datetime nor None.
    """
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise ValueError("Expected datetime value")

    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    else:
        value = value.astimezone(UTC)

    return value.isoformat().replace("+00:00", "Z")


def validate_and_parse_iso_format_datetime_string(value):
    """Parse a timezone-aware ISO-8601 string into a datetime.

    Args:
        value: An ISO-8601 datetime string (a trailing 'Z' is accepted).

    Returns:
        The parsed datetime.

    Raises:
        ValueError: If the string is not valid ISO-8601 or lacks timezone info.
    """
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Datetime query parameter must be a valid ISO datetime")
    if dt.tzinfo is None:
        raise ValueError("Datetime query parameter must include timezone info")
    return dt


def serialize_get_reports_query_params(data):
    """Validate report list query params and map them to repository filter keys.

    Args:
        data: Request query parameters (e.g. ``orderBy``, ``category``, date bounds).

    Returns:
        Dict of validated filters/ordering using repository-side key names.

    Raises:
        ValueError: If any parameter has an unsupported value.
    """
    validated_data = {}
    order = data.get("order", "")
    if order:
        if order not in ["asc", "desc"]:
            raise ValueError(f"Order field should be 'asc' or 'desc'")
        validated_data["order"] = order

    order_by = data.get("orderBy")
    if order_by:
        ordering_fields = {
            "createdAt": "created_at",
            "updatedAt": "updated_at",
            "resolvedAt": "resolved_at",
            "title": "title",
            "category": "category",
            "status": "status",
        }
        if order_by not in ordering_fields:
            raise ValueError(
                f"Order by field should be one of {tuple(ordering_fields)}"
            )
        validated_data["order_by"] = ordering_fields[order_by]

    category = data.get("category")
    if category:
        valid_categories = [
            category["category_name"] for category in repository.get_categories()
        ]
        if category not in valid_categories:
            raise ValueError(f"Category field should be one of {valid_categories}")
        validated_data["category"] = category

    status = data.get("status")
    if status:
        valid_statuses = [status["status_name"] for status in repository.get_statuses()]
        if status not in valid_statuses:
            raise ValueError(f"Status field should be one of {valid_statuses}")
        validated_data["status"] = status

    title = data.get("title")
    if title:
        if not isinstance(title, str):
            raise ValueError(f"Title field should be a string")
        validated_data["title"] = title

    description = data.get("description")
    if description:
        if not isinstance(description, str):
            raise ValueError(f"Description field should be a string")
        validated_data["description"] = description

    created_before = data.get("createdBefore")
    if created_before:
        created_before = validate_and_parse_iso_format_datetime_string(created_before)
        validated_data["created_before"] = created_before

    created_after = data.get("createdAfter")
    if created_after:
        created_after = validate_and_parse_iso_format_datetime_string(created_after)
        validated_data["created_after"] = created_after

    updated_before = data.get("updatedBefore")
    if updated_before:
        updated_before = validate_and_parse_iso_format_datetime_string(updated_before)
        validated_data["updated_before"] = updated_before

    updated_after = data.get("updatedAfter")
    if updated_after:
        updated_after = validate_and_parse_iso_format_datetime_string(updated_after)
        validated_data["updated_after"] = updated_after

    resolved_before = data.get("resolvedBefore")
    if resolved_before:
        resolved_before = validate_and_parse_iso_format_datetime_string(resolved_before)
        validated_data["resolved_before"] = resolved_before

    resolved_after = data.get("resolvedAfter")
    if resolved_after:
        resolved_after = validate_and_parse_iso_format_datetime_string(resolved_after)
        validated_data["resolved_after"] = resolved_after

    return validated_data


def validate_and_save_uploaded_image(file):
    """Validate an uploaded image's extension and save it under a unique name.

    Args:
        file: An uploaded file object, or None if no image was sent.

    Returns:
        The generated filename stored on disk, or None if no file was given.

    Raises:
        ValueError: If the file extension is not allowed.
    """
    if not file:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Image extension should be one of {ALLOWED_IMAGE_EXTENSIONS}")

    img_upload_filename = f"report-images-{uuid.uuid4()}{ext}"
    file.save(os.path.join(REPORT_IMAGES_DIR, img_upload_filename))
    return img_upload_filename
