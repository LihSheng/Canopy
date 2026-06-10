"""Runtime reads and full snapshot replace regression tests (Issue 7, Step 4)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus, SourceBinding
from entity_revision.repository import EntityRevisionRepository
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.api_schema


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
def seed_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="runtime_test_entity",
        display_name="Runtime Test Entity",
        description="Entity for runtime read tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_v1(db_session, seed_entity):
    repo = EntityRevisionRepository(db_session)
    rev = repo.save(
        EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Name",
                    semantic_type="string",
                    is_required=True,
                    is_primary_key=True,
                    sort_order=1,
                ),
            ],
            source_bindings=[
                SourceBinding(
                    property_key="name",
                    source_node_id="src-1",
                    source_field_name="name",
                ),
            ],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "source_type": "table",
                    "name": "src",
                    "reference_id": "r1",
                    "fields": ["name"],
                }
            ],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
    )
    return rev


@pytest.fixture
def seed_published_v2(db_session, seed_entity, seed_published_v1):
    repo = EntityRevisionRepository(db_session)
    v1 = repo.get(seed_published_v1.id)
    v1.status = RevisionStatus.ARCHIVED.value
    v1.updated_at = datetime.now(UTC)
    repo.save(v1)

    rev = repo.save(
        EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="name",
                    display_name="Name",
                    semantic_type="string",
                    is_required=True,
                    is_primary_key=True,
                    sort_order=1,
                ),
                EntityProperty(
                    property_id="p2",
                    property_key="email",
                    display_name="Email",
                    semantic_type="string",
                    is_required=False,
                    sort_order=2,
                ),
            ],
            source_bindings=[
                SourceBinding(
                    property_key="name",
                    source_node_id="src-1",
                    source_field_name="name",
                ),
                SourceBinding(
                    property_key="email",
                    source_node_id="src-1",
                    source_field_name="email",
                ),
            ],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "source_type": "table",
                    "name": "src",
                    "reference_id": "r1",
                    "fields": ["name", "email"],
                }
            ],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
    )
    return rev


class TestRuntimeReads:
    def test_materialized_returns_latest_published_by_default(
        self, client, auth_headers, seed_entity, seed_published_v1, seed_published_v2
    ):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice-v2", "email": "alice@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["row_data"]["name"] == "Alice-v2"

    def test_materialized_pinned_version(self, client, auth_headers, seed_entity, seed_published_v1, seed_published_v2):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice-v1"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                json={"revision_id": seed_published_v1.id},
                headers=auth_headers,
            )

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice-v2", "email": "alice@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                json={"revision_id": seed_published_v2.id},
                headers=auth_headers,
            )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized?version=1",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["row_data"]["name"] == "Alice-v1"

    def test_versions_latest_returns_latest_published(self, client, auth_headers, seed_entity, seed_published_v2):
        resp = client.get(
            f"/api/entities/{seed_entity.id}/versions/latest",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["published_revision"]["revision_number"] == 2

    def test_versions_pinned_returns_archived(self, client, auth_headers, seed_entity, seed_published_v1):
        resp = client.get(
            f"/api/entities/{seed_entity.id}/versions/1",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["pinned_revision"]["revision_number"] == 1
        assert data["pinned_revision"]["status"] == "published"

    def test_runtime_reads_exclude_tombstones_by_default(self, client, auth_headers, seed_entity, seed_published_v2):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a@example.com"},
                {"name": "Bob", "email": "b@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        # Re-materialize with only Alice => Bob becomes tombstone
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a2@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 1
        assert rows[0]["row_data"]["name"] == "Alice"

    def test_runtime_reads_include_tombstones(self, client, auth_headers, seed_entity, seed_published_v2):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a@example.com"},
                {"name": "Bob", "email": "b@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a2@example.com"},
            ]
            client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized?include_tombstones=true",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        rows = resp.json()
        assert len(rows) == 2
        tombstoned = [r for r in rows if r["is_tombstone"]]
        assert len(tombstoned) == 1
        assert tombstoned[0]["row_data"]["name"] == "Bob"

    def test_full_snapshot_replace_updates_existing_rows(self, client, auth_headers, seed_entity, seed_published_v2):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "old@example.com"},
            ]
            resp1 = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp1.json()["rows_inserted"] == 1

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "new@example.com"},
            ]
            resp2 = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp2.json()["rows_updated"] == 1

        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized",
            headers=auth_headers,
        )
        rows = resp.json()
        assert rows[0]["row_data"]["email"] == "new@example.com"

    def test_full_snapshot_replace_tombstones_deleted_rows(self, client, auth_headers, seed_entity, seed_published_v2):
        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a@example.com"},
                {"name": "Bob", "email": "b@example.com"},
            ]
            resp1 = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp1.json()["rows_inserted"] == 2

        with patch("api.routes.entities.build_source_data_reader") as mock_factory:
            mock_factory.return_value = lambda sn: [
                {"name": "Alice", "email": "a2@example.com"},
            ]
            resp2 = client.post(
                f"/api/entities/{seed_entity.id}/materialize",
                headers=auth_headers,
            )
        assert resp2.json()["rows_tombstoned"] == 1

        # Audit read includes tombstone
        resp = client.get(
            f"/api/entities/{seed_entity.id}/materialized?include_tombstones=true",
            headers=auth_headers,
        )
        rows = resp.json()
        tombstoned = [r for r in rows if r["is_tombstone"]]
        assert len(tombstoned) == 1
        assert tombstoned[0]["row_data"]["name"] == "Bob"
