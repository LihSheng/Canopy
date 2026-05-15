from starlette.testclient import TestClient


class TestLoginEndpoint:
    def test_login_success(self, client: TestClient, seed_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "admin@herd.example"
        assert data["user"]["display_name"] == "Admin User"
        assert "token" in data
        assert "expires_at" in data
        assert "herd_token" in response.cookies

    def test_login_wrong_password(self, client: TestClient, seed_user):
        response = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "wrong"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

    def test_login_unknown_email(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "pass"},
        )
        assert response.status_code == 401

    def test_login_invalid_email_format(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "not-an-email", "password": "pass"},
        )
        assert response.status_code == 422

    def test_login_missing_fields(self, client: TestClient):
        response = client.post("/api/auth/login", json={})
        assert response.status_code == 422


class TestLogoutEndpoint:
    def test_logout_clears_cookie(self, client: TestClient):
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out"
        cookie = response.headers.get("set-cookie", "")
        assert 'herd_token=""' in cookie or "herd_token=;" in cookie


class TestSessionEndpoint:
    def test_session_authenticated(self, client: TestClient, seed_user):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )
        token = login_resp.json()["token"]

        response = client.get(
            "/api/auth/session",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"]["email"] == "admin@herd.example"

    def test_session_unauthenticated(self, client: TestClient):
        response = client.get("/api/auth/session")
        assert response.status_code == 401

    def test_session_invalid_token(self, client: TestClient):
        response = client.get(
            "/api/auth/session",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_session_via_cookie(self, client: TestClient, seed_user):
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "admin@herd.example", "password": "admin123"},
        )

        response = client.get(
            "/api/auth/session",
            cookies=login_resp.cookies,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
