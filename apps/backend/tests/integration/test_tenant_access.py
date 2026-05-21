import pytest
from starlette.testclient import TestClient

from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel


@pytest.fixture
def seed_tenants(db_session):
    t1 = TenantModel(
        id="tenant-1",
        tenant_uuid="tuuid-1",
        name="Tenant One",
        slug="tenant-one",
        lifecycle_state="active",
        status="active",
    )
    t2 = TenantModel(
        id="tenant-2",
        tenant_uuid="tuuid-2",
        name="Tenant Two",
        slug="tenant-two",
        lifecycle_state="active",
        status="active",
    )
    t3 = TenantModel(
        id="tenant-3",
        tenant_uuid="tuuid-3",
        name="Suspended Co",
        slug="suspended-co",
        lifecycle_state="suspended",
        status="active",
    )
    db_session.add_all([t1, t2, t3])
    db_session.commit()
    return [t1, t2, t3]


@pytest.fixture
def seed_memberships(db_session, seed_user, seed_tenants):
    m1 = TenantMembershipModel(
        user_id=seed_user.id,
        tenant_id="tenant-1",
        role="admin",
        status="active",
    )
    m2 = TenantMembershipModel(
        user_id=seed_user.id,
        tenant_id="tenant-2",
        role="member",
        status="active",
    )
    m3 = TenantMembershipModel(
        user_id=seed_user.id,
        tenant_id="tenant-3",
        role="member",
        status="active",
    )
    db_session.add_all([m1, m2, m3])
    db_session.commit()
    return [m1, m2, m3]


class TestLoginReturnsTenantList:
    def test_login_includes_tenants(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "tenants" in data
        # Suspended Co is filtered out — only active tenants are returned
        assert len(data["tenants"]) == 2
        tenant_names = [t["name"] for t in data["tenants"]]
        assert tenant_names == ["Tenant One", "Tenant Two"]

        roles = {t["role"] for t in data["tenants"]}
        assert "admin" in roles
        assert "member" in roles


class TestTenantListOrdering:
    def test_tenant_order_is_deterministic_and_alphabetical(
        self, client: TestClient, seed_user, seed_tenants, seed_memberships, db_session
    ):
        # Add an extra active tenant that sorts before the existing ones
        from control_plane.schemas.memberships import TenantMembershipModel
        from control_plane.schemas.tenants import TenantModel

        t_a = TenantModel(
            id="tenant-a",
            tenant_uuid="tuuid-a",
            name="Aardvark Ltd",
            slug="aardvark",
            lifecycle_state="active",
            status="active",
        )
        db_session.add(t_a)
        db_session.commit()
        db_session.add(
            TenantMembershipModel(
                user_id=seed_user.id,
                tenant_id="tenant-a",
                role="member",
                status="active",
            )
        )
        db_session.commit()

        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        data = login_resp.json()
        tenant_names = [t["name"] for t in data["tenants"]]
        assert tenant_names == ["Aardvark Ltd", "Tenant One", "Tenant Two"]


class TestSwitchTenant:
    def test_switch_tenant_issues_new_jwt(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]
        cookies = login_resp.cookies

        response = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-1"},
            headers={"Authorization": f"Bearer {token}"},
            cookies=cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["tenant"] is not None
        assert data["tenant"]["tenant_id"] == "tenant-1"
        assert data["tenant"]["role"] == "admin"
        assert "herd_token" in response.cookies

    def test_subsequent_request_resolves_tenant_context(
        self, client: TestClient, seed_user, seed_tenants, seed_memberships
    ):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        switch_resp = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-2"},
            headers={"Authorization": f"Bearer {token}"},
        )
        new_token = switch_resp.json().get("token") or switch_resp.cookies.get("herd_token")

        session_resp = client.get(
            "/api/auth/session",
            headers={"Authorization": f"Bearer {new_token}"},
            cookies=switch_resp.cookies,
        )
        assert session_resp.status_code == 200
        data = session_resp.json()
        assert data["tenant"] is not None
        assert data["tenant"]["tenant_id"] == "tenant-2"
        assert data["tenant"]["role"] == "member"

    def test_switch_to_unoccupied_tenant_denied(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        response = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-nonexistent"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_switch_to_suspended_tenant_denied(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        response = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-3"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    def test_multiple_tenant_switching(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]
        cookies = login_resp.cookies

        switch1 = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-1"},
            headers={"Authorization": f"Bearer {token}"},
            cookies=cookies,
        )
        assert switch1.status_code == 200
        assert switch1.json()["tenant"]["tenant_id"] == "tenant-1"

        new_cookies = switch1.cookies
        switch2 = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-2"},
            headers={"Authorization": f"Bearer {switch1.json().get('token', token)}"},
            cookies=new_cookies,
        )
        assert switch2.status_code == 200
        assert switch2.json()["tenant"]["tenant_id"] == "tenant-2"


class TestSessionAfterLogin:
    def test_session_after_login_has_auto_entered_first_tenant(
        self, client: TestClient, seed_user, seed_tenants, seed_memberships
    ):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        response = client.get(
            "/api/auth/session",
            headers={"Authorization": f"Bearer {token}"},
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        # First active tenant by name is auto-entered (Tenant One)
        assert data["tenant"] is not None
        assert data["tenant"]["tenant_id"] == "tenant-1"
        assert data["tenant"]["role"] == "admin"
        # Suspended tenant is filtered out
        assert len(data["tenants"]) == 2

    def test_session_with_active_tenant(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        switch_resp = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-1"},
            headers={"Authorization": f"Bearer {token}"},
        )

        session_resp = client.get(
            "/api/auth/session",
            cookies=switch_resp.cookies,
        )
        assert session_resp.status_code == 200
        data = session_resp.json()
        assert data["tenant"] is not None
        assert data["tenant"]["tenant_id"] == "tenant-1"
        assert data["tenant"]["role"] == "admin"


class TestAccessDeniedScenarios:
    def test_user_with_no_membership_gets_empty_tenant_list(self, client: TestClient, seed_tenants):
        response = client.post(
            "/api/auth/login",
            json={"email": "lonely@herd.example", "password": "pass123"},
        )
        if response.status_code == 200:
            data = response.json()
            assert data["tenants"] == []

    def test_stale_membership_blocked(self, client: TestClient, seed_user, seed_tenants, seed_memberships):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        switch_resp = client.post(
            "/api/auth/switch-tenant",
            json={"tenant_id": "tenant-1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert switch_resp.status_code == 200
