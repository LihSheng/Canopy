import uuid
from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.ingestion import (
    CleaningPipelineResponse,
    CleaningStepRequest,
    CleaningStepResponse,
    CreatePipelineRequest,
    MappingDecisionRequest,
    MappingDecisionResponse,
    MappingSuggestionsResponse,
    PipelineValidationResponse,
    ReorderStepsRequest,
    UploadResponse,
    WorkbookProfileResponse,
)
from common.database import get_db
from common.errors import NotFoundError, ValidationError
from v3.ingestion.cleaning import validate_pipeline
from v3.ingestion.domain import CleaningPipeline, CleaningStep, MappingDecision, PipelineStatus
from v3.ingestion.profiling import generate_profile
from v3.ingestion.repository import IngestionRepository
from v3.ingestion.service import process_upload

router = APIRouter(prefix="/api/v3/ingestion", tags=["v3-ingestion"])


@router.post("/uploads", response_model=UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    source_profile: str = Form(...),
    dataset_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> UploadResponse:
    if file.filename is None:
        raise ValidationError("File name is required")

    file_bytes = file.file.read()

    repo = IngestionRepository(db)
    record = process_upload(
        repo=repo,
        file_bytes=file_bytes,
        file_name=file.filename,
        source_profile=source_profile,
        dataset_type=dataset_type,
    )

    return UploadResponse(
        upload_id=record.id,
        status=record.status.value,
        file_name=record.file_name,
        file_size=record.file_size,
        checksum=record.checksum,
        created_at=record.created_at,
    )


@router.get("/uploads/{upload_id}/preview", response_model=WorkbookProfileResponse)
def get_upload_preview(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> WorkbookProfileResponse:
    repo = IngestionRepository(db)
    profile = generate_profile(repo, upload_id)
    return WorkbookProfileResponse(
        upload_id=profile.upload_id,
        best_sheet_name=profile.best_sheet_name,
        sheet_profiles=[
            {
                "sheet_name": s.sheet_name,
                "row_count": s.row_count,
                "column_count": s.column_count,
                "header_row_index": s.header_row_index,
                "confidence": s.confidence,
                "warnings": s.warnings,
            }
            for s in profile.sheet_profiles
        ],
        column_profiles=[
            {
                "source_column_name": c.source_column_name,
                "inferred_type": c.inferred_type,
                "sample_values": c.sample_values,
                "null_ratio": c.null_ratio,
                "confidence": c.confidence,
                "suggested_target_field": c.suggested_target_field,
            }
            for c in profile.column_profiles
        ],
        preview_rows=profile.preview_rows,
        warnings=profile.warnings,
    )


@router.post("/uploads/{upload_id}/mapping", response_model=list[MappingDecisionResponse])
def save_mappings(
    upload_id: str,
    decisions: list[MappingDecisionRequest],
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> list[MappingDecisionResponse]:
    repo = IngestionRepository(db)

    record = repo.get_upload(upload_id)
    if record is None:
        from common.errors import NotFoundError
        raise NotFoundError("Upload not found")

    domain_decisions = [
        MappingDecision(
            source_column_name=d.source_column_name,
            target_field_name=d.target_field_name,
            confirmed=d.confirmed,
            overridden_by_user=d.overridden_by_user,
        )
        for d in decisions
    ]
    repo.save_mapping_decisions(upload_id, domain_decisions)
    return [MappingDecisionResponse(**asdict(d)) for d in domain_decisions]


@router.get("/uploads/{upload_id}/mapping", response_model=MappingSuggestionsResponse)
def get_mappings(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> MappingSuggestionsResponse:
    repo = IngestionRepository(db)

    record = repo.get_upload(upload_id)
    if record is None:
        from common.errors import NotFoundError
        raise NotFoundError("Upload not found")

    saved = repo.get_mapping_decisions(upload_id)
    if saved:
        return MappingSuggestionsResponse(
            upload_id=upload_id,
            decisions=[MappingDecisionResponse(**asdict(d)) for d in saved],
            column_profiles=[],
        )

    profile = generate_profile(repo, upload_id)
    fallback_decisions = [
        MappingDecision(
            source_column_name=c.source_column_name,
            target_field_name=c.suggested_target_field or "",
            confirmed=c.confidence >= 0.7,
            overridden_by_user=False,
        )
        for c in profile.column_profiles
    ]
    return MappingSuggestionsResponse(
        upload_id=upload_id,
        decisions=[MappingDecisionResponse(**asdict(d)) for d in fallback_decisions],
        column_profiles=[
            {
                "source_column_name": c.source_column_name,
                "inferred_type": c.inferred_type,
                "sample_values": c.sample_values,
                "null_ratio": c.null_ratio,
                "confidence": c.confidence,
                "suggested_target_field": c.suggested_target_field,
            }
            for c in profile.column_profiles
        ],
    )


@router.get("/uploads/{upload_id}", response_model=UploadResponse)
def get_upload(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> UploadResponse:
    repo = IngestionRepository(db)
    record = repo.get_upload(upload_id)
    if record is None:
        raise NotFoundError("Upload not found")

    return UploadResponse(
        upload_id=record.id,
        status=record.status.value,
        file_name=record.file_name,
        file_size=record.file_size,
        checksum=record.checksum,
        created_at=record.created_at,
    )


@router.post("/templates", response_model=CleaningPipelineResponse, status_code=201)
def create_pipeline(
    body: CreatePipelineRequest,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> CleaningPipelineResponse:
    repo = IngestionRepository(db)
    record = repo.get_upload(body.upload_id)
    if record is None:
        raise NotFoundError("Upload not found")

    existing = repo.get_pipeline_by_upload(body.upload_id)
    if existing is not None:
        raise ValidationError(f"Pipeline already exists for upload '{body.upload_id}'")

    pipeline = CleaningPipeline(
        id=str(uuid.uuid4()),
        upload_id=body.upload_id,
        steps=[],
        status=PipelineStatus.draft.value,
    )
    saved = repo.save_pipeline(pipeline)
    return CleaningPipelineResponse(
        id=saved.id,
        upload_id=saved.upload_id,
        status=saved.status,
        steps=[],
        created_at=saved.created_at,
        updated_at=saved.updated_at,
    )


@router.get("/templates/{pipeline_id}", response_model=CleaningPipelineResponse)
def get_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> CleaningPipelineResponse:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    return CleaningPipelineResponse(
        id=pipeline.id,
        upload_id=pipeline.upload_id,
        status=pipeline.status,
        steps=[CleaningStepResponse(**asdict(s)) for s in pipeline.steps],
        created_at=pipeline.created_at,
        updated_at=pipeline.updated_at,
    )


@router.put("/templates/{pipeline_id}/steps", response_model=list[CleaningStepResponse])
def replace_steps(
    pipeline_id: str,
    steps: list[CleaningStepRequest],
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> list[CleaningStepResponse]:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    if pipeline.status == PipelineStatus.published.value:
        raise ValidationError("Cannot modify a published pipeline")

    domain_steps = [
        CleaningStep(
            id=str(uuid.uuid4()),
            step_type=s.step_type,
            order=s.order,
            parameters=s.parameters,
            description=s.description,
        )
        for s in steps
    ]

    repo.replace_steps(pipeline_id, domain_steps)
    return [CleaningStepResponse(**asdict(s)) for s in domain_steps]


@router.patch("/templates/{pipeline_id}/steps/reorder", response_model=list[CleaningStepResponse])
def reorder_steps(
    pipeline_id: str,
    body: ReorderStepsRequest,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> list[CleaningStepResponse]:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    if pipeline.status == PipelineStatus.published.value:
        raise ValidationError("Cannot modify a published pipeline")

    reordered = repo.reorder_steps(pipeline_id, body.step_ids)
    return [CleaningStepResponse(**asdict(s)) for s in reordered]


@router.patch("/templates/{pipeline_id}/publish", response_model=CleaningPipelineResponse)
def publish_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> CleaningPipelineResponse:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    if pipeline.status == PipelineStatus.published.value:
        raise ValidationError("Pipeline is already published")

    if not pipeline.steps:
        raise ValidationError("Cannot publish a pipeline with no steps")

    warnings = validate_pipeline(pipeline.steps, PipelineStatus.published.value)
    error_warnings = [w for w in warnings if "error" in w.lower() or "missing" in w.lower()]
    if error_warnings:
        raise ValidationError(f"Cannot publish: {'; '.join(error_warnings)}")

    updated = repo.update_pipeline_status(pipeline_id, PipelineStatus.published)
    if updated is None:
        raise NotFoundError("Pipeline not found")

    return CleaningPipelineResponse(
        id=updated.id,
        upload_id=updated.upload_id,
        status=updated.status,
        steps=[CleaningStepResponse(**asdict(s)) for s in updated.steps],
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post("/templates/{pipeline_id}/validate", response_model=PipelineValidationResponse)
def validate_pipeline_endpoint(
    pipeline_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> PipelineValidationResponse:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    warnings = validate_pipeline(pipeline.steps, pipeline.status)
    return PipelineValidationResponse(warnings=warnings)
