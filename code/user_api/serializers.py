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
        raise ValueError(f"Optional field 'category' must be in {valid_categories}")
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
