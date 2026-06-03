"""Integration tests for dataset retention policy endpoints."""

import pytest

pytestmark = pytest.mark.api_schema


def _create_dataset(client, auth_headers):
    """Helper: create a project, connection, and dataset for testing."""
    proj_resp = client.post("/api/projects/", json={"name": "RetentionTest"}, headers=auth_headers)
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    conn_resp = client.post(
        "/api/connections/",
        json={"project_id": project_id, "source_type": "postgresql", "name": "PG-Ret"},
        headers=auth_headers,
    )
    assert conn_resp.status_code == 201
    conn_id = conn_resp.json()["id"]

    ds_resp = client.post(
        "/api/datasets/",
        json={
            "project_id": project_id,
            "connection_id": conn_id,
            "name": "employees",
            "source_object_name": "employees",
        },
        headers=auth_headers,
    )
    assert ds_resp.status_code == 201
    return ds_resp.json()["id"]


@pytest.fixture
def admin_headers(client, db_session, seed_tenant_and_membership):
    """Seed an admin user and return auth headers."""
    from auth.hashing import hash_password
    from auth.schema import UserModel
    from control_plane.schemas.memberships import TenantMembershipModel

    user = UserModel(
        id="test-admin-1",
        email="testadmin@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Test Admin",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # Create tenant membership so admin user carries tenant context.
    membership = TenantMembershipModel(
        user_id=user.id,
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()

    response = client.post(
        "/api/auth/login",
        json={"email": "testadmin@canopy.dev", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestGetRetentionPolicy:
    def test_returns_default_when_no_policy(self, client, auth_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.get(f"/api/datasets/{ds_id}/retention-policy", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_id"] == ds_id
        assert data["id"] is None
        assert data["mode"] == "retain_indefinitely"
        assert data["is_active"] is False

    def test_returns_saved_policy(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        # Save policy as admin
        put_resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "90_days"},
            headers=admin_headers,
        )
        assert put_resp.status_code == 200

        # GET as regular user (read allowed)
        get_resp = client.get(f"/api/datasets/{ds_id}/retention-policy", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["preset"] == "90_days"
        assert data["mode"] == "expire_after"
        assert data["horizon_days"] == 90
        assert data["is_active"] is True


class TestPutRetentionPolicy:
    def test_admin_can_create_policy(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "30_days"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dataset_id"] == ds_id
        assert data["preset"] == "30_days"
        assert data["mode"] == "expire_after"
        assert data["horizon_days"] == 30
        assert data["is_active"] is True
        assert data["id"] is not None

    def test_admin_can_update_policy(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        # Create
        client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "30_days"},
            headers=admin_headers,
        )

        # Update
        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "1_year"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["preset"] == "1_year"
        assert data["horizon_days"] == 365

    def test_non_admin_cannot_create_policy(self, client, auth_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "30_days"},
            headers=auth_headers,
        )
        assert resp.status_code == 401

    def test_rejects_invalid_preset(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "invalid_preset"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_rejects_destructive_deletion(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "custom", "mode": "purge", "horizon_days": 30},
            headers=admin_headers,
        )
        assert resp.status_code == 400  # v1 rejects destructive deletion

    def test_custom_preset_requires_positive_horizon(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "custom", "mode": "expire_after", "horizon_days": -5},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_custom_preset_with_expire_after(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "custom", "mode": "expire_after", "horizon_days": 180},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["preset"] == "custom"
        assert data["mode"] == "expire_after"
        assert data["horizon_days"] == 180

    def test_calculated_next_action_set_for_finite_policy(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "30_days"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # calculated_next_action_at should be set for finite policies
        assert data["calculated_next_action_at"] is not None

    def test_retain_indefinitely_has_no_next_action(self, client, auth_headers, admin_headers):
        ds_id = _create_dataset(client, auth_headers)

        resp = client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "retain_indefinitely"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["calculated_next_action_at"] is None


class TestRetentionAudit:
    def test_policy_change_writes_audit_event(self, client, auth_headers, admin_headers, db_session):
        ds_id = _create_dataset(client, auth_headers)

        client.put(
            f"/api/datasets/{ds_id}/retention-policy",
            json={"preset": "90_days"},
            headers=admin_headers,
        )

        # Check audit events
        from control_plane.schemas.audit import AuditEventModel

        events = (
            db_session.query(AuditEventModel)
            .filter(AuditEventModel.event_type.in_(["retention.policy.created", "retention.policy.updated"]))
            .all()
        )
        assert len(events) >= 1
        event = events[0]
        assert event.actor_user_id == "test-admin-1"
        assert event.event_type == "retention.policy.created"

        import json

        payload = json.loads(event.event_payload_json) if event.event_payload_json else {}
        assert payload["dataset_id"] == ds_id
        assert payload["preset"] == "90_days"
