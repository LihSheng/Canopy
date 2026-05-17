from sqlalchemy.orm import Session

from v3.ingestion.domain import CleaningPipeline, CleaningStep, MappingDecision, PipelineStatus, UploadRecord, UploadStatus
from v3.ingestion.schema import CleaningPipelineModel, CleaningStepModel, MappingDecisionModel, UploadModel


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

    def save_pipeline(self, pipeline: CleaningPipeline) -> CleaningPipeline:
        model = CleaningPipelineModel(
            id=pipeline.id,
            upload_id=pipeline.upload_id,
            status=pipeline.status,
        )
        self._db.add(model)
        for s in pipeline.steps:
            self._db.add(CleaningStepModel(
                id=s.id,
                pipeline_id=pipeline.id,
                step_type=s.step_type,
                order=s.order,
                parameters=s.parameters,
                description=s.description,
            ))
        self._db.commit()
        return pipeline

    def get_pipeline(self, pipeline_id: str) -> CleaningPipeline | None:
        model = self._db.query(CleaningPipelineModel).filter(CleaningPipelineModel.id == pipeline_id).first()
        if not model:
            return None
        steps = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == pipeline_id
        ).order_by(CleaningStepModel.order).all()
        return self._pipeline_to_domain(model, steps)

    def get_pipeline_by_upload(self, upload_id: str) -> CleaningPipeline | None:
        model = self._db.query(CleaningPipelineModel).filter(
            CleaningPipelineModel.upload_id == upload_id
        ).first()
        if not model:
            return None
        steps = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == model.id
        ).order_by(CleaningStepModel.order).all()
        return self._pipeline_to_domain(model, steps)

    def replace_steps(self, pipeline_id: str, steps: list[CleaningStep]) -> list[CleaningStep]:
        self._db.query(CleaningStepModel).filter(CleaningStepModel.pipeline_id == pipeline_id).delete()
        for s in steps:
            self._db.add(CleaningStepModel(
                id=s.id,
                pipeline_id=pipeline_id,
                step_type=s.step_type,
                order=s.order,
                parameters=s.parameters,
                description=s.description,
            ))
        self._db.commit()
        return steps

    def reorder_steps(self, pipeline_id: str, step_ids: list[str]) -> list[CleaningStep]:
        existing: list[CleaningStepModel] = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == pipeline_id
        ).all()
        id_map = {m.id: m for m in existing}
        for i, sid in enumerate(step_ids):
            if sid in id_map:
                id_map[sid].order = i
        self._db.commit()
        ordered = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == pipeline_id
        ).order_by(CleaningStepModel.order).all()
        return [self._step_to_domain(s) for s in ordered]

    def update_pipeline_status(self, pipeline_id: str, status: PipelineStatus) -> CleaningPipeline | None:
        model = self._db.query(CleaningPipelineModel).filter(CleaningPipelineModel.id == pipeline_id).first()
        if not model:
            return None
        model.status = status.value
        self._db.commit()
        steps = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == pipeline_id
        ).order_by(CleaningStepModel.order).all()
        return self._pipeline_to_domain(model, steps)

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

    def _step_to_domain(self, m: CleaningStepModel) -> CleaningStep:
        return CleaningStep(
            id=m.id,
            step_type=m.step_type,
            order=m.order,
            parameters=dict(m.parameters) if m.parameters else {},
            description=m.description,
        )

    def _pipeline_to_domain(self, m: CleaningPipelineModel, steps: list[CleaningStepModel]) -> CleaningPipeline:
        return CleaningPipeline(
            id=m.id,
            upload_id=m.upload_id,
            status=m.status,
            steps=[self._step_to_domain(s) for s in steps],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
