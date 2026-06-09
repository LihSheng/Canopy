"""Integration tests for link resolution API endpoints."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_materialization.service import EntityMaterializationService, build_source_data_reader
from entity_revision.domain import EntityLink, EntityProperty, EntityRevision, LinkCardinality, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
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
        object_type_key="link_api_test",
        display_name="Link API Test",
        description="Entity for link resolution API tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_target_entity(db_session, tenant_context):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id=tenant_context.tenant_id,
        object_type_key="link_target_test",
        display_name="Link Target Test",
        description="Target entity for link resolution API tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_target(db_session, tenant_context, seed_target_entity):
    repo = EntityRevisionRepository(db_session)
    draft = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_target_entity.id,
        revision_number=1,
        status=RevisionStatus.DRAFT.value,
        properties=[
            EntityProperty(property_id="t1", property_key="id", display_name="ID", is_primary_key=True),
            EntityProperty(property_id="t2", property_key="name", display_name="Name"),
        ],
        source_bindings=[],
        links=[],
        source_nodes=[
            {"source_id": "s1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["id", "name"]}
        ],
        computed_properties=[],
        layout_state={},
        lock_holder_id="test-user",
        locked_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo.save(draft)
    service = EntityRevisionService(repo, ObjectTypeRepository(db_session))
    published = service.publish_draft(seed_target_entity.id, tenant_context.tenant_id)
    # Materialize target rows
    mat_repo = EntityMaterializationRepository(db_session)
    EntityMaterializationService(repo, mat_repo, build_source_data_reader(db_session))
    rows = [
        EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=seed_target_entity.id,
            revision_id=published.id,
            row_id="mgr-1",
            row_data={"id": "mgr-1", "name": "Alice"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        ),
        EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=seed_target_entity.id,
            revision_id=published.id,
            row_id="mgr-2",
            row_data={"id": "mgr-2", "name": "Bob"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        ),
    ]
    mat_repo.save_rows(seed_target_entity.id, published.id, rows)
    return published


@pytest.fixture
def seed_source_entity_with_link(db_session, tenant_context, seed_entity, seed_target_entity, seed_published_target):
    repo = EntityRevisionRepository(db_session)
    draft = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.DRAFT.value,
        properties=[
            EntityProperty(
                property_id="p1", property_key="employee_id", display_name="Employee ID", is_primary_key=True
            ),
            EntityProperty(property_id="p2", property_key="manager_id", display_name="Manager ID"),
        ],
        source_bindings=[],
        links=[
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=seed_target_entity.id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
            ).to_dict()
        ],
        source_nodes=[
            {
                "source_id": "s1",
                "source_type": "table",
                "name": "t1",
                "reference_id": "r1",
                "fields": ["employee_id", "manager_id"],
            }
        ],
        computed_properties=[],
        layout_state={},
        lock_holder_id="test-user",
        locked_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repo.save(draft)
    service = EntityRevisionService(repo, ObjectTypeRepository(db_session))
    published = service.publish_draft(seed_entity.id, tenant_context.tenant_id)
    # Materialize source rows
    mat_repo = EntityMaterializationRepository(db_session)
    rows = [
        EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_id=published.id,
            row_id="emp-1",
            row_data={"employee_id": "emp-1", "manager_id": "mgr-1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        ),
        EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_id=published.id,
            row_id="emp-2",
            row_data={"employee_id": "emp-2", "manager_id": "mgr-2"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        ),
    ]
    mat_repo.save_rows(seed_entity.id, published.id, rows)
    return published


class TestLinkResolutionApi:
    def test_resolve_link_returns_target_row(self, client, auth_headers, seed_entity, seed_source_entity_with_link):
        response = client.get(
            f"/api/entities/{seed_entity.id}/links/link-1/resolve",
            params={"row_id": "emp-1"},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["row_id"] == "mgr-1"
        assert data["row_data"]["name"] == "Alice"

    def test_resolve_batch_returns_map(self, client, auth_headers, seed_entity, seed_source_entity_with_link):
        response = client.post(
            f"/api/entities/{seed_entity.id}/links/link-1/resolve-batch",
            json={"row_ids": ["emp-1", "emp-2"]},
            headers=auth_headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["emp-1"]["row_id"] == "mgr-1"
        assert data["emp-2"]["row_id"] == "mgr-2"

    def test_resolve_optional_link_returns_none(
        self, client, auth_headers, db_session, tenant_context, seed_entity, seed_target_entity
    ):
        # Create source with optional link to target that has no published revision
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[
                EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID"),
            ],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-opt",
                    display_name="Manager",
                    source_property_key="manager_id",
                    target_entity_id=seed_target_entity.id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                    is_optional=True,
                ).to_dict()
            ],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["manager_id"],
                }
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.save(draft)
        service = EntityRevisionService(repo, ObjectTypeRepository(db_session))
        service.publish_draft(seed_entity.id, tenant_context.tenant_id)
        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.save_rows(
            seed_entity.id,
            draft.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=draft.id,
                    row_id="emp-1",
                    row_data={"manager_id": "mgr-1"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        response = client.get(
            f"/api/entities/{seed_entity.id}/links/link-opt/resolve",
            params={"row_id": "emp-1"},
            headers=auth_headers,
        )
        assert response.status_code == 204

    def test_resolve_required_link_missing_target_returns_404(
        self, client, auth_headers, db_session, tenant_context, seed_entity, seed_target_entity, seed_published_target
    ):
        repo = EntityRevisionRepository(db_session)
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[
                EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID"),
            ],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-req",
                    display_name="Manager",
                    source_property_key="manager_id",
                    target_entity_id=seed_target_entity.id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                    is_optional=False,
                ).to_dict()
            ],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["manager_id"],
                }
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        repo.save(draft)
        service = EntityRevisionService(repo, ObjectTypeRepository(db_session))
        published = service.publish_draft(seed_entity.id, tenant_context.tenant_id)
        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.save_rows(
            seed_entity.id,
            published.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=published.id,
                    row_id="emp-1",
                    row_data={"manager_id": "mgr-99"},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        response = client.get(
            f"/api/entities/{seed_entity.id}/links/link-req/resolve",
            params={"row_id": "emp-1"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_resolve_invalid_link_id_returns_404(self, client, auth_headers, seed_entity, seed_source_entity_with_link):
        response = client.get(
            f"/api/entities/{seed_entity.id}/links/nonexistent/resolve",
            params={"row_id": "emp-1"},
            headers=auth_headers,
        )
        assert response.status_code == 404
