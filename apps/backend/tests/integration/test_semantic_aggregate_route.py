from unittest.mock import AsyncMock, MagicMock

import pytest

from common.errors import ValidationError
from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from semantic.aggregation_service import AggregationBucket, AggregationResponse
from semantic.repository import ObjectTypeRepository
from semantic.service import ObjectTypeService

pytestmark = pytest.mark.api_schema


@pytest.fixture(autouse=True)
def tenant_context():
    """Set up and activate a tenant context for all tests."""
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    yield ctx


@pytest.fixture
def seed_object_type(db_session, tenant_context):
    """Create a reusable object type for aggregation tests."""
    service = ObjectTypeService(ObjectTypeRepository(db_session))
    obj = service.create(
        tenant_id=tenant_context.tenant_id,
        object_type_key="test_aggregate_employee",
        display_name="Test Aggregate Employee",
        description="An object type for aggregate tests",
    )
    return obj


@pytest.fixture
def auth_headers_tenant2(client):
    """Auth headers for a user who belongs to tenant-2."""
    # Create tenant-2 with membership
    from auth.hashing import hash_password
    from auth.schema import UserModel

    db_user = UserModel(
        id="test-user-agg-2",
        email="admin-agg2@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Admin Tenant 2",
        is_active=True,
    )
    from common.database import session_factory

    session_cls = session_factory()
    db = session_cls()
    try:
        db.add(db_user)
        tenant2 = TenantModel(
            id="test-tenant-2",
            tenant_uuid="tuuid-test-agg-2",
            name="Tenant Two Agg",
            slug="test-tenant-2-agg",
            lifecycle_state="active",
            status="active",
        )
        db.add(tenant2)
        membership = TenantMembershipModel(
            user_id=db_user.id,
            tenant_id="test-tenant-2",
            role="admin",
            status="active",
        )
        db.add(membership)
        db.commit()
    finally:
        db.close()

    ctx2 = TenantContext(
        tenant_id="test-tenant-2",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx2)

    response = client.post(
        "/api/auth/login",
        json={"email": "admin-agg2@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]

    # Restore tenant-1 context
    ctx1 = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx1)

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_aggregation_service(monkeypatch):
    mock_service = MagicMock()
    mock_service.aggregate = AsyncMock()
    monkeypatch.setattr("api.routes.semantic.AggregationService", lambda db: mock_service)
    return mock_service


class TestSemanticAggregateRoute:
    def test_aggregate_route_not_found(self, client, auth_headers):
        """Should return 404 if the object type does not exist."""
        response = client.post(
            "/api/semantic/object-types/nonexistent-id/aggregate",
            json={
                "object_type_id": "nonexistent-id",
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_aggregate_route_tenant_isolation(self, client, auth_headers_tenant2, seed_object_type):
        """Tenant 2 should not be able to aggregate Tenant 1's object type (should return 404)."""
        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers_tenant2,
        )
        assert response.status_code == 404

    def test_aggregate_route_happy_path(
        self, client, auth_headers, seed_object_type, db_session, mock_aggregation_service
    ):
        """Should successfully return aggregation results."""
        # Setup a dummy semantic mapping in the DB so it is found
        import uuid

        from semantic.domain import PropertyMapping, SemanticMapping
        from semantic.repository import SemanticMappingRepository

        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id="test-tenant-1",
            dataset_id="test-ds",
            dataset_version_id="test-version",
            version_number=1,
            object_type_id=seed_object_type.id,
            object_type_key=seed_object_type.object_type_key,
            properties=[
                PropertyMapping(source_column="dept", property_name="dept", included=True),
                PropertyMapping(source_column="salary", property_name="salary", semantic_type="number", included=True),
            ],
        )
        repo = SemanticMappingRepository(db_session)
        repo.save(mapping)

        # Configure mock response
        mock_response = AggregationResponse(
            object_type=seed_object_type.object_type_key,
            results=[
                AggregationBucket(dimension_value="HR", metric_value=50000.0),
                AggregationBucket(dimension_value="IT", metric_value=120000.0),
            ],
            truncated=False,
        )
        mock_aggregation_service.aggregate.return_value = mock_response

        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "dept",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object_type"] == seed_object_type.object_type_key
        assert len(data["results"]) == 2
        assert data["results"][0]["dimension_value"] == "HR"
        assert data["results"][0]["metric_value"] == 50000.0
        assert data["truncated"] is False

    def test_aggregate_route_validation_error(
        self, client, auth_headers, seed_object_type, db_session, mock_aggregation_service
    ):
        """Should forward service ValidationErrors as 400 Bad Request."""
        import uuid

        from semantic.domain import PropertyMapping, SemanticMapping
        from semantic.repository import SemanticMappingRepository

        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id="test-tenant-1",
            dataset_id="test-ds",
            dataset_version_id="test-version",
            version_number=1,
            object_type_id=seed_object_type.id,
            object_type_key=seed_object_type.object_type_key,
            properties=[
                PropertyMapping(source_column="dept", property_name="dept", included=True),
            ],
        )
        repo = SemanticMappingRepository(db_session)
        repo.save(mapping)

        mock_aggregation_service.aggregate.side_effect = ValidationError("Invalid property selected")

        response = client.post(
            f"/api/semantic/object-types/{seed_object_type.id}/aggregate",
            json={
                "object_type_id": seed_object_type.id,
                "dimension": "invalid_property",
                "metric": {"property": "salary", "type": "sum"},
            },
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Invalid property selected" in response.json()["detail"]
