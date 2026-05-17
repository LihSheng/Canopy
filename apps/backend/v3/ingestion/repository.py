from sqlalchemy.orm import Session

from v3.ingestion.domain import MappingDecision, UploadRecord, UploadStatus
from v3.ingestion.schema import MappingDecisionModel, UploadModel


class IngestionRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_upload(self, record: UploadRecord) -> UploadRecord:
        model = self._to_model(record)
        self._db.add(model)
        self._db.commit()
        return record

    def get_upload(self, upload_id: str) -> UploadRecord | None:
        model = self._db.query(UploadModel).filter(UploadModel.id == upload_id).first()
        return self._to_domain(model) if model else None

    def update_status(self, upload_id: str, status: UploadStatus, error_message: str | None = None) -> UploadRecord | None:
        model = self._db.query(UploadModel).filter(UploadModel.id == upload_id).first()
        if not model:
            return None
        model.status = status.value
        if error_message is not None:
            model.error_message = error_message
        self._db.commit()
        return self._to_domain(model)

    def save_mapping_decisions(self, upload_id: str, decisions: list[MappingDecision]) -> None:
        self._db.query(MappingDecisionModel).filter(MappingDecisionModel.upload_id == upload_id).delete()
        for d in decisions:
            self._db.add(MappingDecisionModel(
                upload_id=upload_id,
                source_column_name=d.source_column_name,
                target_field_name=d.target_field_name,
                confirmed=d.confirmed,
                overridden_by_user=d.overridden_by_user,
            ))
        self._db.commit()

    def get_mapping_decisions(self, upload_id: str) -> list[MappingDecision]:
        models = self._db.query(MappingDecisionModel).filter(MappingDecisionModel.upload_id == upload_id).all()
        return [
            MappingDecision(
                source_column_name=m.source_column_name,
                target_field_name=m.target_field_name,
                confirmed=m.confirmed,
                overridden_by_user=m.overridden_by_user,
            )
            for m in models
        ]

    def _to_model(self, record: UploadRecord) -> UploadModel:
        return UploadModel(
            id=record.id,
            file_name=record.file_name,
            file_size=record.file_size,
            mime_type=record.mime_type,
            storage_path=record.storage_path,
            checksum=record.checksum,
            status=record.status.value,
            source_profile=record.source_profile,
            dataset_type=record.dataset_type,
            error_message=record.error_message,
        )

    def _to_domain(self, model: UploadModel) -> UploadRecord:
        return UploadRecord(
            id=model.id,
            file_name=model.file_name,
            file_size=model.file_size,
            mime_type=model.mime_type,
            storage_path=model.storage_path,
            checksum=model.checksum,
            status=UploadStatus(model.status),
            source_profile=model.source_profile,
            dataset_type=model.dataset_type,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
