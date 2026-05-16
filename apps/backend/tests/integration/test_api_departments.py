import pytest

pytestmark = pytest.mark.api_schema


@pytest.mark.usefixtures("seed_analytics_data")
class TestDepartments:
    def test_requires_auth(self, client):
        response = client.get("/api/departments")
        assert response.status_code == 401

    def test_list_departments(self, client, auth_headers):
        response = client.get("/api/departments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6
        assert data[0]["id"] == "dept-1"
        assert "name" in data[0]
        assert "total_spend" in data[0]

    def test_get_department_detail(self, client, auth_headers):
        response = client.get("/api/departments/dept-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "dept-1"
        assert data["name"] == "Engineering"
        assert data["employee_count"] > 0

    def test_get_department_detail_v2_fields(self, client, auth_headers):
        response = client.get("/api/departments/dept-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "attention_state" in data
        assert data["attention_state"] is None
        assert "ai_summary" in data
        assert data["ai_summary"] is None

    def test_department_detail_v2_contract_shape(self, client, auth_headers):
        response = client.get("/api/departments/dept-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for field in ["id", "name", "total_spend", "payroll_spend", "claims_spend",
                       "change_pct", "employee_count", "attention_state", "ai_summary"]:
            assert field in data, f"Missing field: {field}"

    def test_department_not_found(self, client, auth_headers):
        response = client.get("/api/departments/dept-999", headers=auth_headers)
        assert response.status_code == 404

    def test_department_trends(self, client, auth_headers):
        response = client.get("/api/departments/dept-1/trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 7
        assert "month" in data[0]

    def test_department_employees(self, client, auth_headers):
        response = client.get("/api/departments/dept-1/employees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["name"] == "Alice Chen"

    def test_department_claim_types(self, client, auth_headers):
        response = client.get("/api/departments/dept-1/claim-types", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 4

    def test_department_claims(self, client, auth_headers):
        response = client.get("/api/departments/dept-1/claims", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_claims_endpoint(self, client, auth_headers):
        response = client.get("/api/claims", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 9

    def test_claims_filtered_by_department(self, client, auth_headers):
        response = client.get("/api/claims?department_id=dept-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for claim in data:
            assert claim["department"] == "Engineering"
