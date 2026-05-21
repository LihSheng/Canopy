import pytest
from sqlalchemy.orm import sessionmaker

from tenant_data.base import TenantDataBase
from tenant_data.schemas.__all_models__ import __all__ as all_model_names
from tenant_data.schemas.clean import CleanedRecordModel, DerivedReadModel
from tenant_data.schemas.metadata import (
    JobRunModel,
    LineageEdgeModel,
    LineageNodeModel,
    PublishStateModel,
    StorageObjectModel,
)
from tenant_data.schemas.raw import RawArtifactModel, UploadBatchModel
from tenant_data.schemas.staging import NormalizedRowModel

ALL_TENANT_DATA_MODELS = [
    UploadBatchModel,
    RawArtifactModel,
    NormalizedRowModel,
    CleanedRecordModel,
    DerivedReadModel,
    LineageNodeModel,
    LineageEdgeModel,
    PublishStateModel,
    StorageObjectModel,
    JobRunModel,
]


@pytest.fixture
def td_engine(tenant_data_engine):
    TenantDataBase.metadata.create_all(bind=tenant_data_engine)
    yield tenant_data_engine
    TenantDataBase.metadata.drop_all(bind=tenant_data_engine)


@pytest.fixture
def td_session(td_engine):
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=td_engine)
    session = test_session()
    try:
        yield session
    finally:
        session.close()


class TestTenantDataBaseIsSeparate:
    def test_tenant_data_base_is_not_common_base(self):
        from common.database import Base

        assert TenantDataBase is not Base
        assert issubclass(TenantDataBase.mro()[0], object)

    def test_all_tenant_models_extend_tenant_data_base(self):
        for model in ALL_TENANT_DATA_MODELS:
            assert issubclass(model, TenantDataBase), f"{model.__name__} does not extend TenantDataBase"


class TestEveryModelHasTenantId:
    def test_all_models_have_tenant_id(self):
        for model in ALL_TENANT_DATA_MODELS:
            assert hasattr(model, "tenant_id"), f"{model.__name__} missing tenant_id"

    def test_all_models_tenant_id_is_not_nullable(self):
        for model in ALL_TENANT_DATA_MODELS:
            col = model.__table__.columns["tenant_id"]
            assert not col.nullable, f"{model.__name__}.tenant_id should be NOT NULL"

    def test_all_models_tenant_id_is_indexed(self):
        for model in ALL_TENANT_DATA_MODELS:
            col = model.__table__.columns["tenant_id"]
            assert col.index is True, f"{model.__name__}.tenant_id should be indexed"


class TestModelCreation:
    def test_upload_batch_requires_tenant_id(self, td_session):
        batch = UploadBatchModel(
            tenant_id="tenant-1",
            upload_name="test-upload",
            storage_key="tenants/tenant-1/raw/test.csv",
        )
        td_session.add(batch)
        td_session.commit()
        assert batch.tenant_id == "tenant-1"
        assert batch.status == "pending"
        assert batch.size_bytes == 0
        assert batch.checksum is None

    def test_raw_artifact_requires_tenant_id(self, td_session):
        artifact = RawArtifactModel(
            tenant_id="tenant-1",
            batch_id="batch-1",
            storage_key="tenants/tenant-1/raw/artifact.csv",
            mime_type="text/csv",
            size_bytes=1024,
        )
        td_session.add(artifact)
        td_session.commit()
        assert artifact.tenant_id == "tenant-1"
        assert artifact.is_immutable is True

    def test_normalized_row_requires_tenant_id(self, td_session):
        row = NormalizedRowModel(
            tenant_id="tenant-1",
            source_batch_id="batch-1",
            row_index=0,
            normalized_data_json='{"col": "val"}',
        )
        td_session.add(row)
        td_session.commit()
        assert row.tenant_id == "tenant-1"
        assert row.status == "pending"

    def test_cleaned_record_requires_tenant_id(self, td_session):
        record = CleanedRecordModel(
            tenant_id="tenant-1",
            source_row_id="row-1",
            record_type="employee",
            cleaned_data_json='{"name": "Alice"}',
        )
        td_session.add(record)
        td_session.commit()
        assert record.tenant_id == "tenant-1"
        assert record.is_valid is True

    def test_derived_read_model_requires_tenant_id(self, td_session):
        drm = DerivedReadModel(
            tenant_id="tenant-1",
            model_name="dashboard_summary",
            model_data_json='{"total": 100}',
        )
        td_session.add(drm)
        td_session.commit()
        assert drm.tenant_id == "tenant-1"
        assert drm.is_current is True

    def test_lineage_node_requires_tenant_id(self, td_session):
        node = LineageNodeModel(
            tenant_id="tenant-1",
            node_type="raw_artifact",
            node_ref="batch-1",
        )
        td_session.add(node)
        td_session.commit()
        assert node.tenant_id == "tenant-1"

    def test_lineage_edge_requires_tenant_id(self, td_session):
        edge = LineageEdgeModel(
            tenant_id="tenant-1",
            from_node_id="node-1",
            to_node_id="node-2",
            edge_type="derived_from",
        )
        td_session.add(edge)
        td_session.commit()
        assert edge.tenant_id == "tenant-1"

    def test_publish_state_requires_tenant_id(self, td_session):
        ps = PublishStateModel(
            tenant_id="tenant-1",
            binding_key="dashboard/main",
        )
        td_session.add(ps)
        td_session.commit()
        assert ps.tenant_id == "tenant-1"
        assert ps.is_published is False

    def test_storage_object_requires_tenant_id(self, td_session):
        so = StorageObjectModel(
            tenant_id="tenant-1",
            storage_key="tenants/tenant-1/raw/file.csv",
        )
        td_session.add(so)
        td_session.commit()
        assert so.tenant_id == "tenant-1"
        assert so.lifecycle_state == "active"
        assert so.retention_state == "retained"

    def test_job_run_requires_tenant_id(self, td_session):
        job = JobRunModel(
            tenant_id="tenant-1",
            job_type="ingest",
        )
        td_session.add(job)
        td_session.commit()
        assert job.tenant_id == "tenant-1"
        assert job.status == "pending"


class TestModelDefaults:
    def test_upload_batch_defaults(self, td_session):
        batch = UploadBatchModel(
            tenant_id="t1",
            upload_name="batch1",
            storage_key="key1",
        )
        td_session.add(batch)
        td_session.commit()
        assert batch.size_bytes == 0
        assert batch.status == "pending"
        assert batch.checksum is None

    def test_raw_artifact_defaults(self, td_session):
        artifact = RawArtifactModel(
            tenant_id="t1",
            storage_key="key1",
        )
        td_session.add(artifact)
        td_session.commit()
        assert artifact.size_bytes == 0
        assert artifact.is_immutable is True
        assert artifact.mime_type is None

    def test_derived_read_model_defaults(self, td_session):
        drm = DerivedReadModel(
            tenant_id="t1",
            model_name="summary",
            model_data_json="{}",
        )
        td_session.add(drm)
        td_session.commit()
        assert drm.is_current is True
        assert drm.expires_at is None

    def test_storage_object_defaults(self, td_session):
        so = StorageObjectModel(
            tenant_id="t1",
            storage_key="key1",
        )
        td_session.add(so)
        td_session.commit()
        assert so.size_bytes == 0
        assert so.lifecycle_state == "active"
        assert so.retention_state == "retained"


class TestModelRelationships:
    def test_lineage_edge_links_nodes(self, td_session):
        node1 = LineageNodeModel(
            tenant_id="t1",
            node_type="upload_batch",
            node_ref="batch-1",
        )
        node2 = LineageNodeModel(
            tenant_id="t1",
            node_type="cleaned_record",
            node_ref="record-1",
        )
        td_session.add_all([node1, node2])
        td_session.commit()

        edge = LineageEdgeModel(
            tenant_id="t1",
            from_node_id=node1.id,
            to_node_id=node2.id,
            edge_type="cleaned_from",
        )
        td_session.add(edge)
        td_session.commit()

        assert edge.from_node_id == node1.id
        assert edge.to_node_id == node2.id


class TestAllModelsExported:
    def test_all_model_names_match_implementation(self):
        expected = {m.__name__ for m in ALL_TENANT_DATA_MODELS}
        actual = set(all_model_names)
        assert expected == actual, f"__all_models__ missing: {expected - actual}, extra: {actual - expected}"
