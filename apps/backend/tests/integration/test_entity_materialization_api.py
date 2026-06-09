"""Integration tests for Entity Materialization API."""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus, SourceBinding
from entity_revision.repository import EntityRevisionRepository
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def tenant_context():
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    yield ctx


@pytest.fixture
def seed_tenant_and_membership(db_session, seed_user):
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
        user_id=seed_user.id,
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    return tenant, membership


@pytest.fixture
def auth_headers(client, seed_user, seed_tenant_and_membership):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seed_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="mat_api_entity",
        display_name="Materialization API Entity",
        description="Entity for materialization API tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_revision(db_session, seed_entity):
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="employee_id",
                display_name="Employee ID",
                semantic_type="integer",
                is_required=True,
                is_primary_key=True,
                sort_order=1,
            ),
            EntityProperty(
                property_id="prop-002",
                property_key="employee_name",
                display_name="Employee Name",
                semantic_type="string",
                is_required=True,
                sort_order=2,
            ),
        ],
        source_bindings=[
            SourceBinding(
                property_key="employee_id",
                source_node_id="src-1",
                source_field_name="id",
            ),
            SourceBinding(
                property_key="employee_name",
                source_node_id="src-1",
                source_field_name="name",
            ),
        ],
        links=[],
        source_nodes=[
            {
                "source_id": "src-1",
                "source_type": "dataset_table",
                "name": "employees",
                "reference_id": "ds-001",
                "fields": ["id", "name"],
            }
        ],
        computed_properties=[],
        layout_state={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )
    return repo.save(revision)


@pytest.fixture
def seed_archived_revision(db_session, seed_entity):
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=2,
        status=RevisionStatus.ARCHIVED.value,
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="employee_id",
                display_name="Employee ID",
                semantic_type="integer",
                is_required=True,
                is_primary_key=True,
                sort_order=1,
            ),
            EntityProperty(
                property_id="prop-002",
                property_key="employee_name",
                display_name="Employee Name",
                semantic_type="string",
                is_required=True,
                sort_order=2,
            ),
        ],
        source_bindings=[
            SourceBinding(
                property_key="employee_id",
                source_node_id="src-1",
                source_field_name="id",
            ),
            SourceBinding(
                property_key="employee_name",
                source_node_id="src-1",
                source_field_name="name",
            ),
        ],
        links=[],
        source_nodes=[
            {
                "source_id": "src-1",
                "source_type": "dataset_table",
                "name": "employees",
                "reference_id": "ds-001",
                "fields": ["id", "name"],
            }
        ],
        computed_properties=[],
        layout_state={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )
    return repo.save(revision)


class TestMaterializeAPI:
    """Test POST /entities/{id}/materialize and GET /entities/{id}/materialized."""

    def _mock_reader(self):
        return [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

    def test_materialize_triggers_materialization(self, client, auth_headers, seed_entity, seed_published_revision):
        """POST /entities/{id}/materialize triggers materialization and returns stats."""
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: self._mock_reader()
            response = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["rows_inserted"] == 2
        assert data["rows_updated"] == 0
        assert data["rows_tombstoned"] == 0

    def test_get_materialized_rows_latest(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/materialized returns rows for latest published revision."""
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: self._mock_reader()
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 2
        row_ids = {r["row_id"] for r in data}
        assert "1" in row_ids
        assert "2" in row_ids
        assert data[0]["row_data"]["employee_name"] in {"Alice", "Bob"}

    def test_get_materialized_rows_pinned_version(
        self,
        client,
        auth_headers,
        seed_entity,
        seed_published_revision,
        seed_archived_revision,
    ):
        """GET /entities/{id}/materialized?version={n} returns pinned version rows."""
        # Materialize both revisions with different data
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"id": 1, "name": "Alice-v1"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                json={"revision_id": seed_published_revision.id},
                headers=auth_headers,
            )

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"id": 1, "name": "Alice-v2"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                json={"revision_id": seed_archived_revision.id},
                headers=auth_headers,
            )

        # Pin to version 1
        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized?version=1",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["row_data"]["employee_name"] == "Alice-v1"

        # Pin to version 2
        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized?version=2",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["row_data"]["employee_name"] == "Alice-v2"

    def test_get_materialized_rows_include_tombstones(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/materialized?include_tombstones=true includes tombstones."""
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        # Second run: only Alice remains
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"id": 1, "name": "Alice"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        # Normal read: only Alice
        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        assert len(response.json()) == 1

        # Audit read: Alice + Bob tombstone
        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized?include_tombstones=true",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 2
        tombstoned = [r for r in data if r["is_tombstone"]]
        assert len(tombstoned) == 1
        assert tombstoned[0]["row_id"] == "2"
        assert tombstoned[0]["row_data"]["employee_name"] == "Bob"

    def test_get_materialized_single_row(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/materialized/{row_id} returns a single row."""
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"id": 1, "name": "Alice"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized/1",
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["row_id"] == "1"
        assert data["row_data"]["employee_name"] == "Alice"
        assert data["is_tombstone"] is False

    def test_get_materialized_single_row_not_found(self, client, auth_headers, seed_entity, seed_published_revision):
        """GET /entities/{id}/materialized/{row_id} returns 404 for missing row."""
        response = client.get(
            f"/api/entities/{seed_entity.id}/materialized/999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_materialize_requires_published_revision(self, client, auth_headers, seed_entity):
        """Materializing an entity with no published revision returns 404."""
        response = client.post(
            f"/api/entities/{seed_entity.id}/materialize",
            headers=auth_headers,
        )
        assert response.status_code == 404
