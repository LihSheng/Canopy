import pytest


@pytest.fixture
def seed_db():
    """Bootstrap a test database with minimal seed data."""
    # Placeholder: create tables, insert fixture rows
    yield
    # Cleanup after test


@pytest.fixture
def auth_headers():
    """Return headers for an authenticated test user."""
    return {"Authorization": "Bearer test-token"}
