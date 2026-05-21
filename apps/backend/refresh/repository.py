from sqlalchemy.orm import Session

from common.clock import utcnow
from refresh.domain import DataSnapshot, RefreshJob
from refresh.schema import DataSnapshotModel, RefreshJobModel


class RefreshRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_job(self, job: RefreshJob) -> RefreshJobModel:
        model = RefreshJobModel(
            id=job.id,
            status=job.status,
            current_stage=job.current_stage,
            snapshot_id=job.snapshot_id,
            trigger_type=job.trigger_type,
            requested_by_user_id=job.requested_by_user_id,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def get_job(self, job_id: str) -> RefreshJobModel | None:
        return self._db.query(RefreshJobModel).filter(RefreshJobModel.id == job_id).first()

    def update_job(self, job: RefreshJob) -> RefreshJobModel:
        model = self._db.query(RefreshJobModel).filter(RefreshJobModel.id == job.id).first()
        if model is None:
            raise ValueError(f"Refresh job {job.id} not found")
        model.status = job.status
        model.current_stage = job.current_stage
        model.snapshot_id = job.snapshot_id
        model.finished_at = job.finished_at
        model.error_message = job.error_message
        self._db.commit()
        self._db.refresh(model)
        return model

    def save_data_snapshot(self, snapshot: DataSnapshot) -> DataSnapshotModel:
        from datetime import datetime

        created_at = snapshot.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at) if created_at else utcnow()
        model = DataSnapshotModel(
            id=snapshot.id,
            refresh_job_id=snapshot.refresh_job_id,
            status=snapshot.status,
            created_at=created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def get_current_snapshot(self) -> DataSnapshotModel | None:
        return (
            self._db.query(DataSnapshotModel)
            .filter(DataSnapshotModel.status == "current")
            .order_by(DataSnapshotModel.created_at.desc())
            .first()
        )

    def mark_current_snapshot(self, job_id: str, snapshot_id: str) -> None:
        existing = self._db.query(DataSnapshotModel).filter(DataSnapshotModel.status == "current").all()
        for snap in existing:
            snap.status = "archived"
        new_snap = DataSnapshotModel(
            id=snapshot_id,
            refresh_job_id=job_id,
            status="current",
            created_at=utcnow(),
        )
        self._db.add(new_snap)
        self._db.commit()

    def get_latest_job(self) -> RefreshJobModel | None:
        return self._db.query(RefreshJobModel).order_by(RefreshJobModel.started_at.desc()).first()
