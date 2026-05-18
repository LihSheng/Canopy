import pytest
from sqlalchemy.orm import sessionmaker

from tenant_data.base import TenantDataBase
from tenant_data.rls import (
    ALL_TENANT_DATA_TABLES,
    apply_rls,
    generate_rls_policies,
    generate_rls_rollback,
    is_rls_supported,
)
from tenant_data.schemas.raw import RawArtifactModel, UploadBatchModel
from tenant_data.schemas.staging import NormalizedRowModel
from tenant_data.schemas.clean import CleanedRecordModel, DerivedReadModel
from tenant_data.schemas.metadata import (
    JobRunModel,
    LineageEdgeModel,
    LineageNodeModel,
    PublishStateModel,
    StorageObjectModel,
)


class TestRlsPolicyGeneration:
    def test_generate_rls_policies_produces_valid_sql(self):
        sql = generate_rls_policies(None, ["upload_batches"])
        assert "ENABLE ROW LEVEL SECURITY" in sql
        assert "FORCE ROW LEVEL SECURITY" in sql
        assert "CREATE POLICY tenant_isolation" in sql
        assert "app.current_tenant_id" in sql

    def test_generate_rls_policies_covers_every_tenant_table(self):
        sql = generate_rls_policies(None, ALL_TENANT_DATA_TABLES)
        for table in ALL_TENANT_DATA_TABLES:
            assert table in sql, f"Missing RLS policy for {table}"

    def test_generate_rls_rollback_produces_valid_drop_statements(self):
        sql = generate_rls_rollback(None, ["upload_batches"])
        assert "DROP POLICY IF EXISTS tenant_isolation" in sql
        assert "NO FORCE ROW LEVEL SECURITY" in sql
        assert "DISABLE ROW LEVEL SECURITY" in sql

    def test_generate_rls_rollback_reverses_order(self):
        tables = ["upload_batches", "raw_artifacts"]
        sql = generate_rls_rollback(None, tables)
        idx_batches = sql.find("upload_batches")
        idx_artifacts = sql.find("raw_artifacts")
        assert idx_artifacts < idx_batches

    def test_is_rls_supported_returns_true_for_postgres(self, db_session):
        assert is_rls_supported(db_session) is True

    def test_apply_rls_executes_on_postgres(self, tenant_data_engine):
        TenantDataBase.metadata.create_all(bind=tenant_data_engine)
        factory = sessionmaker(autocommit=False, autoflush=False, bind=tenant_data_engine)
        db_session = factory()
        try:
            apply_rls(db_session, ["upload_batches"])
            db_session.commit()
        finally:
            db_session.close()


class TestPerModelRlsPolicies:
    def test_upload_batch_rls_policy(self):
        sql = UploadBatchModel.get_rls_policy_sql()
        assert "upload_batches" in sql
        assert "tenant_isolation" in sql
        assert "app.current_tenant_id" in sql

    def test_raw_artifact_rls_policy_includes_immutable_check(self):
        sql = RawArtifactModel.get_rls_policy_sql()
        assert "raw_artifacts" in sql
        assert "is_immutable = true" in sql.lower()

    def test_normalized_row_rls_policy(self):
        sql = NormalizedRowModel.get_rls_policy_sql()
        assert "normalized_rows" in sql
        assert "tenant_isolation" in sql

    def test_cleaned_record_rls_policy(self):
        sql = CleanedRecordModel.get_rls_policy_sql()
        assert "cleaned_records" in sql
        assert "tenant_isolation" in sql

    def test_derived_read_model_rls_policy(self):
        sql = DerivedReadModel.get_rls_policy_sql()
        assert "derived_read_models" in sql
        assert "tenant_isolation" in sql

    def test_lineage_node_rls_policy(self):
        sql = LineageNodeModel.get_rls_policy_sql()
        assert "lineage_nodes" in sql

    def test_lineage_edge_rls_policy(self):
        sql = LineageEdgeModel.get_rls_policy_sql()
        assert "lineage_edges" in sql

    def test_publish_state_rls_policy(self):
        sql = PublishStateModel.get_rls_policy_sql()
        assert "publish_states" in sql

    def test_storage_object_rls_policy(self):
        sql = StorageObjectModel.get_rls_policy_sql()
        assert "storage_objects" in sql

    def test_job_run_rls_policy(self):
        sql = JobRunModel.get_rls_policy_sql()
        assert "job_runs" in sql


class TestRlsEdgeCases:
    def test_empty_table_list_produces_empty_sql(self):
        sql = generate_rls_policies(None, [])
        assert sql == ""

    def test_empty_rollback_produces_empty_sql(self):
        sql = generate_rls_rollback(None, [])
        assert sql == ""

    def test_multiple_tables_sql_is_separated(self):
        sql = generate_rls_policies(None, ["t1", "t2"])
        assert sql.count("CREATE POLICY tenant_isolation") == 2
        assert sql.count("ENABLE ROW LEVEL SECURITY") == 2
        assert sql.count("FORCE ROW LEVEL SECURITY") == 2

