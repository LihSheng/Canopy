"""Integration tests for Feature Flags API."""

import pytest

pytestmark = pytest.mark.api_schema


# ─── Fixtures ───


@pytest.fixture
def admin_headers(client, seed_user, db_session):
    """Create a user with is_admin=True and return auth headers.

    Uses a unique email to avoid conflict with the seed_user fixture
    which already creates admin@canopy.dev (without is_admin).
    """
    from auth.hashing import hash_password
    from auth.schema import UserModel

    admin = UserModel(
        id="ff-admin-user-1",
        email="ff-admin@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Feature Flag Admin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "ff-admin@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def non_admin_headers(client, seed_user, db_session):
    """Create a non-admin user and return auth headers.

    Uses a unique email to avoid conflict with seed_user.
    """
    from auth.hashing import hash_password
    from auth.schema import UserModel

    user = UserModel(
        id="ff-regular-user-1",
        email="ff-user@canopy.dev",
        password_hash=hash_password("user123"),
        display_name="Feature Flag Regular User",
        is_admin=False,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "ff-user@canopy.dev", "password": "user123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ─── Public endpoint tests ───


class TestPublicFeatureFlagsEndpoint:
    def test_returns_enabled_flags_map(self, client, non_admin_headers):
        """GET /api/feature-flags returns a map of flag_key -> enabled."""
        response = client.get("/api/feature-flags", headers=non_admin_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, dict)
        # Default flag should be seeded
        assert data["entity_canvas_enabled"] is True

    def test_requires_authentication(self, client):
        """Public endpoint still requires authentication."""
        response = client.get("/api/feature-flags")
        assert response.status_code == 401, response.text


# ─── Admin endpoint tests ───


class TestAdminListFeatureFlags:
    def test_admin_can_list_flags(self, client, admin_headers):
        """Admin can list all feature flags with descriptions."""
        response = client.get("/api/admin/feature-flags", headers=admin_headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert any(f["flag_key"] == "entity_canvas_enabled" for f in data)

    def test_non_admin_cannot_list_flags(self, client, non_admin_headers):
        """Non-admin users get a 401."""
        response = client.get("/api/admin/feature-flags", headers=non_admin_headers)
        assert response.status_code == 401, response.text

    def test_unauthenticated_cannot_list_flags(self, client):
        """Unauthenticated requests get a 401."""
        response = client.get("/api/admin/feature-flags")
        assert response.status_code == 401, response.text


class TestAdminToggleFeatureFlag:
    def test_admin_toggle_flag_on(self, client, admin_headers):
        """Admin can toggle a flag to enabled."""
        response = client.put(
            "/api/admin/feature-flags/entity_canvas_enabled",
            headers=admin_headers,
            json={"enabled": True},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["flag_key"] == "entity_canvas_enabled"
        assert data["enabled"] is True

    def test_admin_toggle_flag_off(self, client, admin_headers):
        """Admin can toggle a flag to disabled."""
        response = client.put(
            "/api/admin/feature-flags/entity_canvas_enabled",
            headers=admin_headers,
            json={"enabled": False},
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["flag_key"] == "entity_canvas_enabled"
        assert data["enabled"] is False

    def test_non_admin_cannot_toggle_flag(self, client, non_admin_headers):
        """Non-admin users get a 401 when toggling."""
        response = client.put(
            "/api/admin/feature-flags/entity_canvas_enabled",
            headers=non_admin_headers,
            json={"enabled": False},
        )
        assert response.status_code == 401, response.text

    def test_toggle_unknown_flag_returns_404(self, client, admin_headers):
        """Toggling a non-existent flag returns 404."""
        response = client.put(
            "/api/admin/feature-flags/nonexistent_flag",
            headers=admin_headers,
            json={"enabled": True},
        )
        assert response.status_code == 404, response.text

    def test_toggle_persists_across_requests(self, client, admin_headers):
        """Toggle state persists after the request."""
        # Turn off
        r1 = client.put(
            "/api/admin/feature-flags/entity_canvas_enabled",
            headers=admin_headers,
            json={"enabled": False},
        )
        assert r1.status_code == 200

        # Verify via list
        r2 = client.get("/api/admin/feature-flags", headers=admin_headers)
        flags = r2.json()
        canvas_flag = next(f for f in flags if f["flag_key"] == "entity_canvas_enabled")
        assert canvas_flag["enabled"] is False

        # Verify via public endpoint
        r3 = client.get("/api/feature-flags", headers=admin_headers)
        public_map = r3.json()
        assert public_map["entity_canvas_enabled"] is False


# ─── Seed behavior ───


class TestSeedDefaults:
    def test_seed_creates_default_flags(self, client, admin_headers):
        """Default flags are created on first access."""
        # Clear any existing flags from the DB
        response = client.get("/api/admin/feature-flags", headers=admin_headers)
        assert response.status_code == 200
        flags = response.json()
        assert any(f["flag_key"] == "entity_canvas_enabled" for f in flags)
        canvas_flag = next(f for f in flags if f["flag_key"] == "entity_canvas_enabled")
        assert canvas_flag["enabled"] is True
        assert len(canvas_flag["description"]) > 0

    def test_seed_is_idempotent(self, client, admin_headers):
        """Calling seed multiple times does not duplicate or overwrite."""
        # First call
        r1 = client.get("/api/admin/feature-flags", headers=admin_headers)
        assert r1.status_code == 200
        count1 = len(r1.json())

        # Second call
        r2 = client.get("/api/admin/feature-flags", headers=admin_headers)
        assert r2.status_code == 200
        count2 = len(r2.json())

        assert count1 == count2
