from common.errors import NotFoundError
from connection.repository import ConnectionRepository
from dataset.domain import DatasetStatus
from dataset.repository import DatasetRepository


class LineageMetadataService:
    def __init__(self, connection_repo: ConnectionRepository, dataset_repo: DatasetRepository):
        self._connection_repo = connection_repo
        self._dataset_repo = dataset_repo

    def get_connection_lineage(self, connection_id: str) -> dict:
        connection = self._connection_repo.get(connection_id)
        if connection is None:
            raise NotFoundError("Connection not found")

        datasets = self._dataset_repo.list_by_connection(connection_id)

        nodes: list[dict] = []
        edges: list[dict] = []

        external_source_node_id = f"external_source_{connection_id}"
        nodes.append(
            {
                "id": external_source_node_id,
                "type": "external_source",
                "label": connection.name,
                "state": "materialized",
            }
        )

        for ds in datasets:
            raw_node_id = f"raw_dataset_{ds.id}"
            state = (
                "pending"
                if (ds.status == DatasetStatus.PENDING_INITIAL_RUN.value or ds.active_version_id is None)
                else "materialized"
            )
            nodes.append(
                {
                    "id": raw_node_id,
                    "type": "raw_dataset",
                    "label": ds.name,
                    "state": state,
                    "dataset_id": ds.id,
                }
            )
            edges.append({"from": external_source_node_id, "to": raw_node_id, "type": "feeds"})

        return {"nodes": nodes, "edges": edges}
