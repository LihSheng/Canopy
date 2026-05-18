import pytest
from sqlalchemy.orm import sessionmaker

from v5.tenant_data.base import TenantDataBase
from v5.tenant_data.schemas.raw import UploadBatchModel
from v5.tenant_data.tenant_aware_query import tenant_scoped_query


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


class TestTenantDataIsolation:
    def test_insert_data_for_tenant_a(self, td_session):
        batch = UploadBatchModel(
            tenant_id="tenant-a",
            upload_name="upload-a",
            storage_key="key-a",
        )
        td_session.add(batch)
        td_session.commit()

        result = td_session.query(UploadBatchModel).filter(
            UploadBatchModel.tenant_id == "tenant-a"
        ).first()
        assert result is not None
        assert result.tenant_id == "tenant-a"

    def test_tenant_scoped_query_filters_by_tenant(self, td_session):
        batch_a = UploadBatchModel(
            tenant_id="tenant-a",
            upload_name="upload-a-1",
            storage_key="key-a-1",
        )
        batch_b = UploadBatchModel(
            tenant_id="tenant-b",
            upload_name="upload-b-1",
            storage_key="key-b-1",
        )
        td_session.add_all([batch_a, batch_b])
        td_session.commit()

        results_a = tenant_scoped_query(
            td_session, UploadBatchModel, "tenant-a"
        ).all()
        assert len(results_a) == 1
        assert all(r.tenant_id == "tenant-a" for r in results_a)

        results_b = tenant_scoped_query(
            td_session, UploadBatchModel, "tenant-b"
        ).all()
        assert len(results_b) == 1
        assert all(r.tenant_id == "tenant-b" for r in results_b)

    def test_cross_tenant_access_blocked_by_scoped_query(self, td_session):
        batch_a = UploadBatchModel(
            tenant_id="tenant-a",
            upload_name="upload-a-2",
            storage_key="key-a-2",
        )
        td_session.add(batch_a)
        td_session.commit()

        results = tenant_scoped_query(
            td_session, UploadBatchModel, "tenant-b"
        ).all()
        assert len(results) == 0

    def test_direct_query_without_tenant_filter_returns_all(self, td_session):
        batch_a = UploadBatchModel(
            tenant_id="tenant-a",
            upload_name="upload-a-3",
            storage_key="key-a-3",
        )
        batch_b = UploadBatchModel(
            tenant_id="tenant-b",
            upload_name="upload-b-3",
            storage_key="key-b-3",
        )
        td_session.add_all([batch_a, batch_b])
        td_session.commit()

        all_results = td_session.query(UploadBatchModel).all()
        assert len(all_results) == 2

    def test_transaction_rolls_back_on_error(self, td_session):
        batch = UploadBatchModel(
            tenant_id="tenant-rollback",
            upload_name="should-rollback",
            storage_key="key-rollback",
        )
        try:
            td_session.add(batch)
            td_session.flush()
            raise ValueError("simulated error")
        except ValueError:
            td_session.rollback()

        results = td_session.query(UploadBatchModel).filter(
            UploadBatchModel.tenant_id == "tenant-rollback"
        ).all()
        assert len(results) == 0

    def test_tenant_context_isolated_per_transaction(self, td_session):
        batch_a = UploadBatchModel(
            tenant_id="tenant-a",
            upload_name="tx-a",
            storage_key="key-tx-a",
        )
        batch_b = UploadBatchModel(
            tenant_id="tenant-b",
            upload_name="tx-b",
            storage_key="key-tx-b",
        )
        td_session.add_all([batch_a, batch_b])
        td_session.commit()

        q_a = tenant_scoped_query(td_session, UploadBatchModel, "tenant-a")
        assert q_a.count() == 1
        assert q_a.first().upload_name == "tx-a"

        q_b = tenant_scoped_query(td_session, UploadBatchModel, "tenant-b")
        assert q_b.count() == 1
        assert q_b.first().upload_name == "tx-b"

    def test_multiple_tenants_data_does_not_leak(self, td_session):
        for i in range(5):
            batch = UploadBatchModel(
                tenant_id=f"tenant-{i}",
                upload_name=f"upload-{i}",
                storage_key=f"key-{i}",
            )
            td_session.add(batch)
        td_session.commit()

        for i in range(5):
            results = tenant_scoped_query(
                td_session, UploadBatchModel, f"tenant-{i}"
            ).all()
            assert len(results) == 1
            assert results[0].tenant_id == f"tenant-{i}"
