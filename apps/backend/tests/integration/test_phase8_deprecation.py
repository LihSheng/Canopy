"""Deprecation behavior regression tests (Issue 7, Step 7)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
from semantic.domain import ObjectType, PropertyMapping, SemanticMapping
from semantic.repository import ObjectTypeRepository, SemanticMappingRepository

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
        object_type_key="deprecation_test_entity",
        display_name="Deprecation Test Entity",
        description="Entity for deprecation tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published(db_session, seed_entity):
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
                    sort_order=1,
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
def seed_mapping(db_session, tenant_context, seed_entity):
    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="deprecation-ds",
        dataset_version_id="deprecation-v1",
        version_number=1,
        object_type_id=seed_entity.id,
        object_type_key=seed_entity.object_type_key,
        properties=[
            PropertyMapping(
                source_column="name",
                property_name="name",
                semantic_type="string",
                included=True,
                is_primary_key=False,
            ),
        ],
        links=[],
        computed_properties=[],
        source_nodes=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo = SemanticMappingRepository(db_session)
    return repo.save(mapping)


class TestDeprecationBehavior:
    def test_deprecate_sets_status(self, client, auth_headers, seed_entity, seed_published):
        resp = client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["deprecated"] is True
        assert data["status"] == "deprecated"

    def test_deprecated_excluded_from_normal_listing(
        self, client, auth_headers, seed_entity, seed_published, seed_mapping
    ):
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        resp = client.get("/api/entities", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert not any(item["id"] == seed_entity.id for item in data)

    def test_deprecated_included_in_historical_listing(
        self, client, auth_headers, seed_entity, seed_published, seed_mapping
    ):
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        resp = client.get("/api/entities?include_deprecated=true", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(item["id"] == seed_entity.id for item in data)

    def test_deprecated_entity_detail_still_accessible(
        self, client, auth_headers, seed_entity, seed_published, seed_mapping
    ):
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        resp = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["id"] == seed_entity.id

    def test_deprecated_materialized_rows_still_accessible(
        self, client, auth_headers, db_session, seed_entity, seed_published
    ):
        from entity_materialization.domain import EntityMaterializedRow
        from entity_materialization.repository import EntityMaterializationRepository

        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.save_rows(
            seed_entity.id,
            seed_published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=seed_published.id,
                    row_id="row-1",
                    row_data={"name": "Alice"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
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

    @pytest.mark.xfail(reason="Deprecated entity guardrail not yet implemented")
    def test_deprecated_cannot_fork_new_draft(self, client, auth_headers, seed_entity, seed_published, seed_mapping):
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text

    @pytest.mark.xfail(reason="Deprecated entity guardrail not yet implemented")
    def test_deprecated_cannot_publish_again(self, client, auth_headers, seed_entity, seed_published, seed_mapping):
        # Create a draft first
        client.post(
            f"/api/entities/{seed_entity.id}/draft",
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/deprecate",
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
