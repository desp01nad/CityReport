import pytest

from db_repository import repository

# Mirrors the categories and statuses seeded by db/seed-db.sql.
CATEGORIES = [
    {"category_id": 1, "category_name": "Generic"},
    {"category_id": 2, "category_name": "Road Damage"},
    {"category_id": 3, "category_name": "Street Lighting"},
    {"category_id": 4, "category_name": "Cleanliness"},
]
STATUSES = [
    {"status_id": 1, "status_name": "Reported"},
    {"status_id": 2, "status_name": "In Progress"},
    {"status_id": 3, "status_name": "Resolved"},
    {"status_id": 4, "status_name": "Rejected"},
]


@pytest.fixture(autouse=True)
def stub_repository_lookups(monkeypatch):
    """Serve the category and status lookups from fixtures instead of the database.

    The serializers validate ``category`` and ``status`` against the repository,
    so every test would otherwise need a live PostgreSQL connection.
    """
    monkeypatch.setattr(repository, "get_categories", lambda: CATEGORIES)
    monkeypatch.setattr(repository, "get_statuses", lambda: STATUSES)
