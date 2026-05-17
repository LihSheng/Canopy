from sqlalchemy.orm import Session

from common.errors import NotFoundError
from v3.ingestion.schema import (
    CleanedSnapshotModel as V3CleanedSnapshotModel,
    LineageEdgeModel as V3LineageEdgeModel,
    LineageNodeModel as V3LineageNodeModel,
    UploadModel as V3UploadModel,
    WorkflowStateModel as V3WorkflowStateModel,
)


class MigrationService:
    def __init__(self, db: Session):
        self._db = db

    def map_upload_to_connection(self, upload_id: str) -> dict:
        upload = self._db.query(V3UploadModel).filter(V3UploadModel.id == upload_id).first()
        if upload is None:
            raise NotFoundError("Upload not found")
        return {
            "id": upload.id,
            "project_id": upload.source_profile,
            "source_type": "static_file",
            "name": upload.file_name,
            "status": "active",
            "config_json": {
                "file_size": upload.file_size,
                "mime_type": upload.mime_type,
                "storage_path": upload.storage_path,
                "checksum": upload.checksum,
                "dataset_type": upload.dataset_type,
            },
            "created_at": upload.created_at.isoformat(),
            "updated_at": upload.updated_at.isoformat() if upload.updated_at else None,
            "_v3_type": "upload",
        }

    def map_upload_to_datasets(self, upload_id: str) -> list[dict]:
        upload = self._db.query(V3UploadModel).filter(V3UploadModel.id == upload_id).first()
        if upload is None:
            raise NotFoundError("Upload not found")
        return [{
            "id": upload.id,
            "project_id": upload.source_profile,
            "connection_id": upload.id,
            "name": upload.dataset_type or upload.file_name,
            "source_object_name": upload.file_name,
            "status": "active",
            "active_version_id": None,
            "created_at": upload.created_at.isoformat(),
            "updated_at": upload.updated_at.isoformat() if upload.updated_at else None,
            "_v3_type": "dataset",
        }]

    def map_snapshot_to_version(self, snapshot_id: str) -> dict:
        snapshot = self._db.query(V3CleanedSnapshotModel).filter(V3CleanedSnapshotModel.id == snapshot_id).first()
        if snapshot is None:
            raise NotFoundError("Snapshot not found")
        return {
            "id": snapshot.id,
            "dataset_id": snapshot.upload_id,
            "run_id": None,
            "version_number": 1,
            "status": "ready" if snapshot.status == "completed" else "failed",
            "row_count": snapshot.row_count,
            "column_count": 0,
            "storage_path": snapshot.storage_path,
            "created_at": snapshot.created_at.isoformat(),
            "_v3_type": "dataset_version",
        }

    def map_workflow_to_runs(self, upload_id: str) -> list[dict]:
        workflows = self._db.query(V3WorkflowStateModel).filter(V3WorkflowStateModel.upload_id == upload_id).all()
        if not workflows:
            return []

        _status_map = {
            "started": "queued",
            "processing": "running",
            "completed": "completed",
            "failed": "failed",
        }
        runs = []
        for wf in workflows:
            runs.append({
                "id": wf.upload_id,
                "project_id": "",
                "connection_id": wf.upload_id,
                "dataset_id": wf.upload_id,
                "status": _status_map.get(wf.status, "queued"),
                "started_by": "",
                "started_at": wf.created_at.isoformat(),
                "finished_at": wf.updated_at.isoformat() if wf.status in ("completed", "failed") else None,
                "duration_ms": 0,
                "warning_count": 0,
                "error_message": wf.error_message or "",
                "created_at": wf.created_at.isoformat(),
                "current_step": wf.current_step,
                "completed_steps": wf.completed_steps or [],
                "_v3_type": "run",
            })
        return runs

    def get_v4_lineage(self, upload_id: str) -> dict:
        nodes = self._db.query(V3LineageNodeModel).filter(V3LineageNodeModel.upload_id == upload_id).all()
        edges = self._db.query(V3LineageEdgeModel).filter(V3LineageEdgeModel.upload_id == upload_id).all()
        return {
            "nodes": [
                {
                    "id": n.id,
                    "node_type": n.node_type,
                    "label": n.label,
                    "meta_data": n.meta_data,
                    "created_at": n.created_at.isoformat(),
                }
                for n in nodes
            ],
            "edges": [
                {
                    "id": e.id,
                    "source_node_id": e.from_node_id,
                    "target_node_id": e.to_node_id,
                    "edge_type": e.edge_type,
                    "meta_data": e.meta_data,
                    "created_at": e.created_at.isoformat(),
                }
                for e in edges
            ],
        }

    def list_migratable_uploads(self) -> list[dict]:
        uploads = self._db.query(V3UploadModel).order_by(V3UploadModel.created_at.desc()).all()
        result = []
        for u in uploads:
            wf = self._db.query(V3WorkflowStateModel).filter(V3WorkflowStateModel.upload_id == u.id).first()
            snapshot_count = self._db.query(V3CleanedSnapshotModel).filter(V3CleanedSnapshotModel.upload_id == u.id).count()
            result.append({
                "upload_id": u.id,
                "file_name": u.file_name,
                "dataset_type": u.dataset_type,
                "source_profile": u.source_profile,
                "upload_status": u.status,
                "workflow_status": wf.status if wf else None,
                "snapshot_count": snapshot_count,
                "created_at": u.created_at.isoformat(),
            })
        return result
