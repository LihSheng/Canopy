from connection.domain import Connection
from connection.repository import ConnectionRepository
from dataset.domain import Dataset, DatasetStatus, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository
from dataset.service import DatasetService


def test_refresh_dataset_version_api(client, auth_headers, db_session, monkeypatch):
    connection_repo = ConnectionRepository(db_session)
    dataset_repo = DatasetRepository(db_session)

    connection_repo.save(
        Connection(
            id="conn-1",
            project_id="proj-1",
            source_type="postgresql",
            name="Payroll DB",
            config_json={},
        ),
    )
    dataset_repo.save(
        Dataset(
            id="dataset-1",
            project_id="proj-1",
            connection_id="conn-1",
            name="Payroll",
            source_object_name="payroll",
            status=DatasetStatus.ACTIVE.value,
        ),
    )

    async def _fake_materialize(self, connection, dataset, source_object_name):
        return DatasetVersion(
            id="version-2",
            dataset_id=dataset.id,
            run_id=None,
            version_number=2,
            status=DatasetVersionStatus.READY.value,
            row_count=12,
            column_count=4,
            storage_path="/tmp/version-2.jsonl",
            raw_storage_path="/tmp/version-2.jsonl",
            cleaning_issues=[],
        )

    monkeypatch.setattr(DatasetService, "_materialize_database_dataset_version_async", _fake_materialize)

    response = client.post("/api/datasets/dataset-1/refresh", headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "version-2"
    assert data["version_number"] == 2
    assert data["status"] == DatasetVersionStatus.READY.value

    updated_dataset = dataset_repo.get("dataset-1")
    assert updated_dataset is not None
    assert updated_dataset.active_version_id == "version-2"
