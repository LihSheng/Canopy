"""Registry search and detail regression tests (Issue 7, Step 8)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import (
    ComputedProperty,
    EntityLink,
    EntityProperty,
    EntityRevision,
    LinkCardinality,
    RevisionStatus,
)
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
        object_type_key="registry_test_entity",
        display_name="Registry Test Entity",
        description="Entity for registry search tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_deprecated_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="deprecated_registry_entity",
        display_name="Deprecated Registry Entity",
        description="Deprecated entity for registry tests",
        status="deprecated",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_mapping_for_entity(db_session, tenant_context, seed_entity):
    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="registry-ds",
        dataset_version_id="registry-v1",
        version_number=1,
        object_type_id=seed_entity.id,
        object_type_key=seed_entity.object_type_key,
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="id",
                semantic_type="string",
                included=True,
                is_primary_key=True,
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


@pytest.fixture
def seed_mapping_for_deprecated(db_session, tenant_context, seed_deprecated_entity):
    mapping = SemanticMapping(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        dataset_id="deprecated-registry-ds",
        dataset_version_id="deprecated-registry-v1",
        version_number=1,
        object_type_id=seed_deprecated_entity.id,
        object_type_key=seed_deprecated_entity.object_type_key,
        properties=[
            PropertyMapping(
                source_column="id",
                property_name="id",
                semantic_type="string",
                included=True,
                is_primary_key=True,
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


class TestRegistrySearch:
    def test_search_by_display_name(self, client, auth_headers, seed_entity, seed_mapping_for_entity):
        resp = client.get("/api/entities?q=Registry+Test", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(seed_entity.display_name in item["display_name"] for item in data)

    def test_search_by_object_type_key(self, client, auth_headers, seed_entity, seed_mapping_for_entity):
        resp = client.get(f"/api/entities?q={seed_entity.object_type_key}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(item["object_type_key"] == seed_entity.object_type_key for item in data)

    def test_search_does_not_include_computed_property_values(
        self, client, auth_headers, db_session, tenant_context, seed_entity
    ):
        # Publish a revision with a computed property
        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="salary",
                        display_name="Salary",
                        semantic_type="number",
                    ),
                ],
                computed_properties=[
                    ComputedProperty(
                        id="cp1",
                        property_key="total_comp",
                        display_name="Total Compensation",
                        formula="salary * 1.1",
                        formula_type="arithmetic",
                        inputs=["salary"],
                        output_type="number",
                        is_active=True,
                    ),
                ],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        # Search by formula text should not match
        resp = client.get("/api/entities?q=salary%20*%201.1", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert not any(item["id"] == seed_entity.id for item in data)

    def test_search_excludes_deprecated_by_default(
        self, client, auth_headers, seed_deprecated_entity, seed_mapping_for_deprecated
    ):
        resp = client.get("/api/entities?q=deprecated_registry", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert not any(item["id"] == seed_deprecated_entity.id for item in data)

    def test_search_include_deprecated(self, client, auth_headers, seed_deprecated_entity, seed_mapping_for_deprecated):
        resp = client.get("/api/entities?q=deprecated_registry&include_deprecated=true", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert any(item["id"] == seed_deprecated_entity.id for item in data)


class TestEntityDetailExtras:
    def test_detail_returns_field_groups(self, client, auth_headers, db_session, tenant_context, seed_entity):
        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
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
                    ),
                ],
                computed_properties=[
                    ComputedProperty(
                        id="cp1",
                        property_key="upper_name",
                        display_name="Upper Name",
                        formula="upper(name)",
                        formula_type="arithmetic",
                        inputs=["name"],
                        output_type="string",
                        is_active=True,
                    ),
                ],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        resp = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "field_groups" in data
        kinds = {fg["field_kind"] for fg in data["field_groups"]}
        assert "base" in kinds
        assert "computed" in kinds

    def test_detail_returns_materialized_preview(self, client, auth_headers, db_session, tenant_context, seed_entity):
        rev_repo = EntityRevisionRepository(db_session)
        rev = rev_repo.save(
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
                    ),
                ],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.save_rows(
            seed_entity.id,
            rev.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=rev.id,
                    row_id=f"row-{i}",
                    row_data={"name": f"Name-{i}"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                )
                for i in range(7)
            ],
        )
        resp = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "materialized_preview" in data
        assert len(data["materialized_preview"]) == 5

    def test_detail_returns_link_status(self, client, auth_headers, db_session, tenant_context, seed_entity):
        # Create target entity and publish
        target_repo = ObjectTypeRepository(db_session)
        target = target_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="detail_target",
                display_name="Detail Target",
                description="Target",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=target.id,
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
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        # Source entity with link
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="ref_id",
                        display_name="Ref ID",
                    ),
                ],
                links=[
                    EntityLink(
                        link_id="link-1",
                        display_name="Target Link",
                        source_property_key="ref_id",
                        target_entity_id=target.id,
                        target_property_key="id",
                        cardinality=LinkCardinality.ONE_TO_ONE.value,
                        is_optional=False,
                        is_active=True,
                    ).to_dict(),
                ],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )
        resp = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "link_status" in data
        assert len(data["link_status"]) == 1
        assert data["link_status"][0]["link_id"] == "link-1"
        assert data["link_status"][0]["resolvable"] is True

    def test_detail_returns_computed_property_warnings_for_draft(
        self, client, auth_headers, db_session, tenant_context, seed_entity
    ):
        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_number=2,
                status=RevisionStatus.DRAFT.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="salary",
                        display_name="Salary",
                        semantic_type="number",
                    ),
                ],
                computed_properties=[
                    ComputedProperty(
                        id="cp1",
                        property_key="bad",
                        display_name="Bad",
                        formula="multiply(missing_prop, 2)",
                        formula_type="arithmetic",
                        inputs=["missing_prop"],
                        output_type="number",
                        is_active=True,
                    ),
                ],
                layout_state={},
                lock_holder_id="user-1",
                locked_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        resp = client.get(f"/api/entities/{seed_entity.id}", headers=auth_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "draft_revision" in data
        warnings = data["draft_revision"]["computed_property_warnings"]
        assert warnings is not None
        assert len(warnings) == 1
        assert "missing_prop" in warnings[0]
