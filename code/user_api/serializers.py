from db_repository import repository


def serialize_create_report_request_data(data):
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
        category["categoryname"]: category["categoryid"]
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
            category["categoryname"]: category["categoryid"]
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
