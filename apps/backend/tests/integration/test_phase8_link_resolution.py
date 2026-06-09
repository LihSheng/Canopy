"""Link validation and resolution regression tests (Issue 7, Step 5)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import (
    EntityProperty,
    EntityRevision,
    LinkCardinality,
    RevisionStatus,
)
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
        object_type_key="link_test_entity",
        display_name="Link Test Entity",
        description="Entity for link tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_target(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="link_target",
        display_name="Link Target",
        description="Target entity for link tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_target_published(db_session, tenant_context, seed_target):
    repo = EntityRevisionRepository(db_session)
    rev = repo.save(
        EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_target.id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="t1",
                    property_key="id",
                    display_name="ID",
                    is_primary_key=True,
                ),
            ],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["id"],
                }
            ],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
    )
    # Materialize target rows
    mat_repo = EntityMaterializationRepository(db_session)
    mat_repo.save_rows(
        seed_target.id,
        rev.id,
        [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_target.id,
                revision_id=rev.id,
                row_id="target-1",
                row_data={"id": "target-1"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_target.id,
                revision_id=rev.id,
                row_id="target-2",
                row_data={"id": "target-2"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ],
    )
    return rev


def _create_source_draft(client, auth_headers, seed_entity):
    resp = client.post(
        f"/api/entities/{seed_entity.id}/revisions",
        json={
            "properties": [
                {
                    "property_id": "p1",
                    "property_key": "name",
                    "display_name": "Name",
                    "semantic_type": "string",
                    "is_required": True,
                    "is_primary_key": True,
                    "sort_order": 1,
                },
                {
                    "property_id": "p2",
                    "property_key": "ref_id",
                    "display_name": "Ref ID",
                    "semantic_type": "string",
                    "is_required": False,
                    "sort_order": 2,
                },
            ],
            "source_nodes": [
                {
                    "source_id": "src-1",
                    "source_type": "table",
                    "name": "src",
                    "reference_id": "r1",
                    "fields": ["name", "ref_id"],
                }
            ],
            "source_bindings": [
                {
                    "property_key": "name",
                    "source_node_id": "src-1",
                    "source_field_name": "name",
                },
                {
                    "property_key": "ref_id",
                    "source_node_id": "src-1",
                    "source_field_name": "ref_id",
                },
            ],
            "links": [],
            "computed_properties": [],
            "layout_state": {},
            "publish": False,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


class TestLinkValidation:
    def test_one_to_one_link_passes_publish(
        self, client, auth_headers, seed_entity, seed_target, seed_target_published
    ):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-1",
                        "display_name": "Link",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_one_to_many_link_passes_publish(
        self, client, auth_headers, seed_entity, seed_target, seed_target_published
    ):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-1",
                        "display_name": "Link",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_MANY.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_many_to_many_rejected_at_publish(self, client, auth_headers, seed_entity):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-bad",
                        "display_name": "Bad",
                        "source_property_key": "ref_id",
                        "target_entity_id": str(uuid.uuid4()),
                        "target_property_key": "id",
                        "cardinality": "M:M",
                        "is_optional": True,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        assert "cardinality" in resp.json()["detail"].lower()

    def test_optional_link_allowed_when_target_not_published(self, client, auth_headers, seed_entity, seed_target):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-opt",
                        "display_name": "Optional",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": True,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text

    def test_required_link_fails_when_target_not_published(self, client, auth_headers, seed_entity, seed_target):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-req",
                        "display_name": "Required",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        resp = client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400, resp.text
        detail = resp.json()["detail"].lower()
        assert "not published" in detail or "target entity" in detail


class TestLinkResolution:
    def test_resolve_one_to_one(
        self, client, auth_headers, db_session, seed_entity, seed_target, seed_target_published
    ):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-1",
                        "display_name": "Link",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        # Materialize source rows directly via repo (bypass reader)
        mat_repo = EntityMaterializationRepository(db_session)
        published = EntityRevisionRepository(db_session).get_published(seed_entity.id)
        mat_repo.save_rows(
            seed_entity.id,
            published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=published.id,
                    row_id="source-1",
                    row_data={"name": "Alice", "ref_id": "target-1"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/links/link-1/resolve",
            params={"row_id": "source-1"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["row_id"] == "target-1"

    def test_resolve_one_to_many_returns_list(
        self, client, auth_headers, db_session, seed_entity, seed_target, seed_target_published
    ):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-1m",
                        "display_name": "Link 1M",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_MANY.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        published = EntityRevisionRepository(db_session).get_published(seed_entity.id)
        mat_repo.save_rows(
            seed_entity.id,
            published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=published.id,
                    row_id="source-1",
                    row_data={"name": "Alice", "ref_id": "target-1"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/links/link-1m/resolve",
            params={"row_id": "source-1"},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["row_id"] == "target-1"

    def test_resolve_optional_returns_none(self, client, auth_headers, db_session, seed_entity, seed_target):
        # Target has no published revision
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-opt",
                        "display_name": "Optional",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": True,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        published = EntityRevisionRepository(db_session).get_published(seed_entity.id)
        mat_repo.save_rows(
            seed_entity.id,
            published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=published.id,
                    row_id="source-1",
                    row_data={"name": "Alice", "ref_id": "missing"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/links/link-opt/resolve",
            params={"row_id": "source-1"},
            headers=auth_headers,
        )
        assert resp.status_code == 204

    def test_resolve_required_missing_target_raises_404(
        self, client, auth_headers, db_session, seed_entity, seed_target, seed_target_published
    ):
        _create_source_draft(client, auth_headers, seed_entity)
        client.put(
            f"/api/entities/{seed_entity.id}/draft",
            json={
                "links": [
                    {
                        "link_id": "link-req",
                        "display_name": "Required",
                        "source_property_key": "ref_id",
                        "target_entity_id": seed_target.id,
                        "target_property_key": "id",
                        "cardinality": LinkCardinality.ONE_TO_ONE.value,
                        "is_optional": False,
                        "is_active": True,
                    }
                ],
            },
            headers=auth_headers,
        )
        client.post(
            f"/api/entities/{seed_entity.id}/draft/publish",
            headers=auth_headers,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        published = EntityRevisionRepository(db_session).get_published(seed_entity.id)
        mat_repo.save_rows(
            seed_entity.id,
            published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=published.id,
                    row_id="source-1",
                    row_data={"name": "Alice", "ref_id": "missing-id"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        resp = client.get(
            f"/api/entities/{seed_entity.id}/links/link-req/resolve",
            params={"row_id": "source-1"},
            headers=auth_headers,
        )
        assert resp.status_code == 404
