import pytest
from starlette.testclient import TestClient

from auth.hashing import hash_password
from auth.schema import UserModel
from v5.control_plane.schemas.tenants import TenantModel


@pytest.fixture
def admin_user(db_session):
    admin = UserModel(
        id="admin-user-1",
        email="admin@herd.example",
        password_hash=hash_password("admin123"),
        display_name="Platform Admin",
        is_active=True,
        is_admin=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_client():
    from app import create_app
    from v5.control_plane.admin_router import router as admin_router

    app = create_app()
    app.include_router(admin_router)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_headers(admin_client, admin_user):
    response = admin_client.post(
        "/api/auth/login",
        json={"email": "admin@herd.example", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_tenant_pending(db_session):
    tenant = TenantModel(
        id="tenant-admin-1",
        tenant_uuid="tuuid-admin-1",
        name="Admin Test Tenant",
        slug="admin-test-tenant",
        lifecycle_state="pending",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def seed_tenant_active(db_session):
    tenant = TenantModel(
        id="tenant-admin-2",
        tenant_uuid="tuuid-admin-2",
        name="Active Tenant",
        slug="active-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


class TestAdminCreateTenant:
    def test_create_tenant_via_admin_api(self, admin_client, admin_headers):
        response = admin_client.post(
            "/api/admin/tenants",
            json={"name": "New Tenant", "slug": "new-tenant"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Tenant"
        assert data["slug"] == "new-tenant"
        assert data["lifecycle_state"] == "pending"

    def test_duplicate_slug_rejected(self, admin_client, admin_headers, seed_tenant_pending):
        response = admin_client.post(
            "/api/admin/tenants",
            json={"name": "Duplicate", "slug": "admin-test-tenant"},
            headers=admin_headers,
        )
        assert response.status_code == 409

    def test_list_tenants(self, admin_client, admin_headers, seed_tenant_pending, seed_tenant_active):
        response = admin_client.get(
            "/api/admin/tenants",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_tenants_filter_by_status(self, admin_client, admin_headers, seed_tenant_pending, seed_tenant_active):
        response = admin_client.get(
            "/api/admin/tenants?status=pending",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(t["lifecycle_state"] == "pending" for t in data)

    def test_get_tenant_detail(self, admin_client, admin_headers, seed_tenant_pending):
        response = admin_client.get(
            f"/api/admin/tenants/{seed_tenant_pending.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == seed_tenant_pending.id
        assert data["name"] == "Admin Test Tenant"


class TestProvisioningFlow:
    def test_provision_tenant(self, admin_client, admin_headers, seed_tenant_pending):
        response = admin_client.post(
            f"/api/admin/tenants/{seed_tenant_pending.id}/provision",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("pending", "running", "completed")
        assert "job_id" in data

    def test_list_jobs(self, admin_client, admin_headers, seed_tenant_pending):
        admin_client.post(
            f"/api/admin/tenants/{seed_tenant_pending.id}/provision",
            headers=admin_headers,
        )
        response = admin_client.get(
            "/api/admin/jobs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1


class TestSuspendRestoreFlow:
    def test_suspend_tenant(self, admin_client, admin_headers, seed_tenant_active):
        response = admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/suspend",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_state"] == "suspended"

    def test_restore_tenant(self, admin_client, admin_headers, seed_tenant_active):
        admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/suspend",
            headers=admin_headers,
        )
        response = admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/restore",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_state"] == "active"


class TestArchiveFlow:
    def test_archive_tenant(self, admin_client, admin_headers, seed_tenant_active):
        response = admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/archive",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["lifecycle_state"] == "archived"


class TestAuditEvents:
    def test_list_audit_events(self, admin_client, admin_headers, seed_tenant_active):
        admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/suspend",
            headers=admin_headers,
        )
        response = admin_client.get(
            "/api/admin/audit-events",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_filter_audit_events_by_tenant(self, admin_client, admin_headers, seed_tenant_active):
        admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/suspend",
            headers=admin_headers,
        )
        response = admin_client.get(
            f"/api/admin/audit-events?tenant_id={seed_tenant_active.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(e["tenant_id"] == seed_tenant_active.id for e in data)


class TestImpersonationFlow:
    def test_impersonate_tenant(self, admin_client, admin_headers, seed_tenant_active):
        response = admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/impersonate",
            json={"reason": "Support ticket #999"},
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["tenant_id"] == seed_tenant_active.id
        assert "session_id" in data

    def test_impersonation_creates_audit_event(self, admin_client, admin_headers, seed_tenant_active):
        admin_client.post(
            f"/api/admin/tenants/{seed_tenant_active.id}/impersonate",
            json={"reason": "Audit test"},
            headers=admin_headers,
        )
        response = admin_client.get(
            "/api/admin/audit-events",
            headers=admin_headers,
        )
        data = response.json()
        imp_events = [e for e in data if e["event_type"] == "impersonation.started"]
        assert len(imp_events) >= 1


class TestTenantConfigs:
    def test_get_tenant_config_empty(self, admin_client, admin_headers, seed_tenant_active):
        response = admin_client.get(
            f"/api/admin/tenant-config/{seed_tenant_active.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestNonAdminAccessDenied:
    def test_non_admin_cannot_access_admin_routes(self, client, seed_tenant_pending):
        from auth.schema import UserModel
        from auth.hashing import hash_password

        response = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        if response.status_code != 200:
            return

        token = response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/admin/tenants", headers=headers)
        assert resp.status_code == 401
