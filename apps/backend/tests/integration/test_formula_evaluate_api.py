"""Integration tests for computed property evaluate API (Step 11)."""

import uuid

import pytest

from auth.hashing import hash_password
from auth.schema import UserModel
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_revision.domain import EntityProperty
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def auth_headers(client, db_session):
    """Override conftest auth_headers to avoid stale session issues."""
    user = UserModel(
        id="test-user-1",
        email="admin@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(user)
    tenant = TenantModel(
        id="test-tenant-1",
        tenant_uuid="tuuid-test-1",
        name="Test Tenant",
        slug="test-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    membership = TenantMembershipModel(
        user_id="test-user-1",
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


class TestFormulaEvaluateApi:
    def test_evaluate_valid_formula(self, client, auth_headers, db_session):
        """POST /entities/{id}/computed-properties/evaluate with valid formula returns result."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="eval_test",
                display_name="Eval Test",
                description="Eval",
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="test-user-1",
        )

        payload = {
            "formula": "multiply(salary, 2)",
            "inputs": ["salary"],
            "sample_row": {"salary": 5000},
        }

        response = client.post(
            f"/api/entities/{entity_id}/computed-properties/evaluate",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["result"] == 10000
        assert data["errors"] == []

    def test_evaluate_invalid_formula_returns_errors(self, client, auth_headers, db_session):
        """Invalid formula returns errors."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="eval_invalid",
                display_name="Eval Invalid",
                description="Eval",
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id="test-tenant-1",
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="test-user-1",
        )

        payload = {
            "formula": "foobar(salary)",
            "inputs": ["salary"],
            "sample_row": {"salary": 5000},
        }

        response = client.post(
            f"/api/entities/{entity_id}/computed-properties/evaluate",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["result"] is None
        assert len(data["errors"]) > 0

    def test_evaluate_without_auth_returns_401(self, client, db_session):
        """Missing auth returns 401."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id="test-tenant-1",
                object_type_key="eval_auth",
                display_name="Eval Auth",
                description="Eval",
            )
        )

        payload = {
            "formula": "upper(salary)",
            "inputs": ["salary"],
            "sample_row": {"salary": "alice"},
        }

        response = client.post(
            f"/api/entities/{entity_id}/computed-properties/evaluate",
            json=payload,
        )

        assert response.status_code == 401
