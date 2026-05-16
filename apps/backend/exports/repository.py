from sqlalchemy.orm import Session

from common.clock import utcnow
from exports.domain import ExportJob
from exports.schema import ExportJobModel


class ExportRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_job(self, job: ExportJob) -> ExportJobModel:
        model = ExportJobModel(
            id=job.id,
            status=job.status,
            preset_name=job.preset_name,
            snapshot_id=job.snapshot_id,
            time_range=job.time_range,
            snapshot_timestamp=job.snapshot_timestamp,
            requested_by_user_id=job.requested_by_user_id,
            include_departments=job.include_departments,
            include_anomalies=job.include_anomalies,
            file_path=job.file_path,
            file_size_bytes=job.file_size_bytes,
            started_at=job.started_at,
            finished_at=job.finished_at,
            error_message=job.error_message,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def get_job(self, job_id: str) -> ExportJobModel | None:
        return (
            self._db.query(ExportJobModel)
            .filter(ExportJobModel.id == job_id)
            .first()
        )

    def update_job(self, job: ExportJob) -> ExportJobModel:
        model = (
            self._db.query(ExportJobModel)
            .filter(ExportJobModel.id == job.id)
            .first()
        )
        if model is None:
            raise ValueError(f"Export job {job.id} not found")
        model.status = job.status
        model.snapshot_id = job.snapshot_id
        model.file_path = job.file_path
        model.file_size_bytes = job.file_size_bytes
        model.finished_at = job.finished_at
        model.error_message = job.error_message
        self._db.commit()
        self._db.refresh(model)
        return model

    def get_recent_jobs(self, limit: int = 20) -> list[ExportJobModel]:
        return (
            self._db.query(ExportJobModel)
            .order_by(ExportJobModel.started_at.desc())
            .limit(limit)
            .all()
        )
