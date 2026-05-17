from datetime import datetime

from sqlalchemy.orm import Session

from v3.ingestion.domain import (
    CleaningPipeline,
    CleaningStep,
    MappingDecision,
    PipelineStatus,
    TemplateFamily,
    TemplateVersion,
    UploadRecord,
    UploadStatus,
)
from v3.ingestion.schema import (
    CleaningPipelineModel,
    CleaningStepModel,
    MappingDecisionModel,
    TemplateFamilyModel,
    TemplateVersionModel,
    UploadModel,
)


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

    def save_template_family(self, family: TemplateFamily) -> TemplateFamily:
        model = TemplateFamilyModel(
            id=family.id,
            dataset_type=family.dataset_type,
            source_profile=family.source_profile,
            name=family.name,
            description=family.description,
            status=family.status,
        )
        self._db.add(model)
        self._db.commit()
        return family

    def get_template_family(self, family_id: str) -> TemplateFamily | None:
        model = self._db.query(TemplateFamilyModel).filter(TemplateFamilyModel.id == family_id).first()
        return self._family_to_domain(model) if model else None

    def list_template_families(self, dataset_type: str | None = None, source_profile: str | None = None) -> list[TemplateFamily]:
        q = self._db.query(TemplateFamilyModel)
        if dataset_type:
            q = q.filter(TemplateFamilyModel.dataset_type == dataset_type)
        if source_profile:
            q = q.filter(TemplateFamilyModel.source_profile == source_profile)
        models = q.order_by(TemplateFamilyModel.created_at.desc()).all()
        return [self._family_to_domain(m) for m in models]

    def update_template_family_status(self, family_id: str, status: str) -> TemplateFamily | None:
        model = self._db.query(TemplateFamilyModel).filter(TemplateFamilyModel.id == family_id).first()
        if not model:
            return None
        model.status = status
        self._db.commit()
        return self._family_to_domain(model)

    def save_template_version(self, version: TemplateVersion) -> TemplateVersion:
        model = TemplateVersionModel(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            state=version.state,
            spec_json=version.spec_json,
            published_at=version.published_at,
        )
        self._db.add(model)
        self._db.commit()
        return version

    def get_template_version(self, version_id: str) -> TemplateVersion | None:
        model = self._db.query(TemplateVersionModel).filter(TemplateVersionModel.id == version_id).first()
        return self._version_to_domain(model) if model else None

    def list_template_versions(self, template_id: str) -> list[TemplateVersion]:
        models = self._db.query(TemplateVersionModel).filter(
            TemplateVersionModel.template_id == template_id
        ).order_by(TemplateVersionModel.version_number.desc()).all()
        return [self._version_to_domain(m) for m in models]

    def get_latest_published_version(self, template_id: str) -> TemplateVersion | None:
        model = self._db.query(TemplateVersionModel).filter(
            TemplateVersionModel.template_id == template_id,
            TemplateVersionModel.state == "published",
        ).order_by(TemplateVersionModel.version_number.desc()).first()
        return self._version_to_domain(model) if model else None

    def update_version_state(self, version_id: str, state: str, published_at: datetime | None = None) -> TemplateVersion | None:
        model = self._db.query(TemplateVersionModel).filter(TemplateVersionModel.id == version_id).first()
        if not model:
            return None
        model.state = state
        if published_at is not None:
            model.published_at = published_at
        self._db.commit()
        return self._version_to_domain(model)

    def bind_upload_to_version(self, pipeline_id: str, template_version_id: str) -> CleaningPipeline | None:
        model = self._db.query(CleaningPipelineModel).filter(CleaningPipelineModel.id == pipeline_id).first()
        if not model:
            return None
        model.template_version_id = template_version_id
        self._db.commit()
        steps = self._db.query(CleaningStepModel).filter(
            CleaningStepModel.pipeline_id == pipeline_id
        ).order_by(CleaningStepModel.order).all()
        return self._pipeline_to_domain(model, steps)

    def _family_to_domain(self, m: TemplateFamilyModel) -> TemplateFamily:
        return TemplateFamily(
            id=m.id,
            dataset_type=m.dataset_type,
            source_profile=m.source_profile,
            name=m.name,
            description=m.description,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _version_to_domain(self, m: TemplateVersionModel) -> TemplateVersion:
        return TemplateVersion(
            id=m.id,
            template_id=m.template_id,
            version_number=m.version_number,
            state=m.state,
            spec_json=dict(m.spec_json) if m.spec_json else {},
            created_at=m.created_at,
            updated_at=m.updated_at,
            published_at=m.published_at,
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
            template_version_id=m.template_version_id,
            steps=[self._step_to_domain(s) for s in steps],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
