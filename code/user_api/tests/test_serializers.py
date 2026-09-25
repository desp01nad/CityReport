from datetime import UTC, datetime

import pytest

from user_api.serializers import serialize_get_reports_query_params


def test_no_params_produce_no_filters():
    assert serialize_get_reports_query_params({}) == {}


def test_valid_order_is_passed_through():
    assert serialize_get_reports_query_params({"order": "asc"}) == {"order": "asc"}


def test_invalid_order_is_rejected():
    with pytest.raises(ValueError, match="'asc' or 'desc'"):
        serialize_get_reports_query_params({"order": "sideways"})


@pytest.mark.parametrize(
    ("order_by", "expected_column"),
    [
        ("createdAt", "created_at"),
        ("updatedAt", "updated_at"),
        ("resolvedAt", "resolved_at"),
        ("title", "title"),
        ("category", "category"),
        ("status", "status"),
    ],
)
def test_order_by_is_mapped_to_a_repository_column(order_by, expected_column):
    validated = serialize_get_reports_query_params({"orderBy": order_by})

    assert validated == {"order_by": expected_column}


def test_unknown_order_by_field_is_rejected():
    with pytest.raises(ValueError, match="Order by field"):
        serialize_get_reports_query_params({"orderBy": "quality"})


def test_seeded_category_and_status_are_passed_through():
    validated = serialize_get_reports_query_params(
        {"category": "Road Damage", "status": "In Progress"}
    )

    assert validated == {"category": "Road Damage", "status": "In Progress"}


def test_unknown_category_is_rejected():
    with pytest.raises(ValueError, match="Category field"):
        serialize_get_reports_query_params({"category": "Potholes"})


def test_unknown_status_is_rejected():
    with pytest.raises(ValueError, match="Status field"):
        serialize_get_reports_query_params({"status": "Closed"})


@pytest.mark.parametrize(
    ("param", "expected_key"),
    [
        ("createdBefore", "created_before"),
        ("createdAfter", "created_after"),
        ("updatedBefore", "updated_before"),
        ("updatedAfter", "updated_after"),
        ("resolvedBefore", "resolved_before"),
        ("resolvedAfter", "resolved_after"),
    ],
)
def test_datetime_bounds_are_parsed_and_renamed(param, expected_key):
    validated = serialize_get_reports_query_params({param: "2026-01-01T00:00:00Z"})

    assert validated == {expected_key: datetime(2026, 1, 1, tzinfo=UTC)}


def test_malformed_datetime_is_rejected():
    with pytest.raises(ValueError, match="valid ISO datetime"):
        serialize_get_reports_query_params({"createdAfter": "last Tuesday"})


def test_datetime_without_timezone_is_rejected():
    with pytest.raises(ValueError, match="must include timezone info"):
        serialize_get_reports_query_params({"createdAfter": "2026-01-01T00:00:00"})


def test_params_combine_and_unknown_ones_are_ignored():
    validated = serialize_get_reports_query_params(
        {
            "order": "desc",
            "orderBy": "updatedAt",
            "category": "Cleanliness",
            "status": "Resolved",
            "title": "pothole",
            "description": "sidewalk",
            "resolvedAfter": "2026-05-06T16:40:00Z",
            "somethingElse": "ignored",
        }
    )

    assert validated == {
        "order": "desc",
        "order_by": "updated_at",
        "category": "Cleanliness",
        "status": "Resolved",
        "title": "pothole",
        "description": "sidewalk",
        "resolved_after": datetime(2026, 5, 6, 16, 40, tzinfo=UTC),
    }
