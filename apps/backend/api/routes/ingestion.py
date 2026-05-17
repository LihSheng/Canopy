import uuid
from dataclasses import asdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.ingestion import (
    BindTemplateRequest,
    CleanedSnapshotResponse,
    CleaningPipelineResponse,
    CleaningStepRequest,
    CleaningStepResponse,
    CreatePipelineRequest,
    CreateTemplateVersionRequest,
    LineageGraphResponse,
    MappingDecisionRequest,
    MappingDecisionResponse,
    MappingSuggestionsResponse,
    PipelineValidationResponse,
    ProcessUploadResponse,
    ReorderStepsRequest,
    TemplateFamilyDetailResponse,
    TemplateFamilyRequest,
    TemplateFamilyResponse,
    TemplateVersionListResponse,
    TemplateVersionResponse,
    UploadResponse,
    WorkbookProfileResponse,
)
from common.database import get_db
from common.errors import NotFoundError, ValidationError
from v3.ingestion.cleaning import validate_pipeline
from v3.ingestion.domain import (
    CleanedSnapshot,
    CleanedSnapshotStatus,
    CleaningPipeline,
    CleaningStep,
    MappingDecision,
    PipelineStatus,
    TemplateFamily,
    TemplateFamilyStatus,
)
from v3.ingestion.engine import execute_cleaning_pipeline, load_raw_rows, parse_spec_steps, save_cleaned_rows
from v3.ingestion.lineage import build_lineage_graph
from v3.ingestion.normalization import normalize_cleaned_rows
from v3.ingestion.profiling import generate_profile
from v3.ingestion.repository import IngestionRepository
from v3.ingestion.service import process_upload
from v3.ingestion.templates import create_draft_version, publish_version, validate_bind

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


@router.get("/template-families", response_model=list[TemplateFamilyResponse])
def list_template_families(
    dataset_type: str | None = None,
    source_profile: str | None = None,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> list[TemplateFamilyResponse]:
    repo = IngestionRepository(db)
    families = repo.list_template_families(dataset_type, source_profile)
    return [TemplateFamilyResponse(**asdict(f)) for f in families]


@router.post("/template-families", response_model=TemplateFamilyResponse, status_code=201)
def create_template_family(
    body: TemplateFamilyRequest,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateFamilyResponse:
    family = TemplateFamily(
        id=str(uuid.uuid4()),
        dataset_type=body.dataset_type,
        source_profile=body.source_profile,
        name=body.name,
        description=body.description,
        status=TemplateFamilyStatus.active.value,
    )
    repo = IngestionRepository(db)
    saved = repo.save_template_family(family)
    return TemplateFamilyResponse(**asdict(saved))


@router.get("/template-families/{template_id}", response_model=TemplateFamilyDetailResponse)
def get_template_family(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateFamilyDetailResponse:
    repo = IngestionRepository(db)
    family = repo.get_template_family(template_id)
    if family is None:
        raise NotFoundError("Template family not found")

    versions = repo.list_template_versions(template_id)
    return TemplateFamilyDetailResponse(
        **asdict(family),
        versions=[TemplateVersionResponse(**asdict(v)) for v in versions],
    )


@router.get("/template-families/{template_id}/versions", response_model=TemplateVersionListResponse)
def list_template_versions(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateVersionListResponse:
    repo = IngestionRepository(db)
    family = repo.get_template_family(template_id)
    if family is None:
        raise NotFoundError("Template family not found")

    versions = repo.list_template_versions(template_id)
    return TemplateVersionListResponse(
        template_id=template_id,
        versions=[TemplateVersionResponse(**asdict(v)) for v in versions],
    )


@router.get("/template-families/{template_id}/versions/{version_id}", response_model=TemplateVersionResponse)
def get_template_version(
    template_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateVersionResponse:
    repo = IngestionRepository(db)
    version = repo.get_template_version(version_id)
    if version is None or version.template_id != template_id:
        raise NotFoundError("Template version not found")

    return TemplateVersionResponse(**asdict(version))


@router.post("/template-families/{template_id}/versions", response_model=TemplateVersionResponse, status_code=201)
def create_template_version(
    template_id: str,
    body: CreateTemplateVersionRequest,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateVersionResponse:
    repo = IngestionRepository(db)
    family = repo.get_template_family(template_id)
    if family is None:
        raise NotFoundError("Template family not found")

    existing_versions = repo.list_template_versions(template_id)

    spec = dict(body.spec_json) if body.spec_json else {}
    if body.clone_from_version_id:
        source = repo.get_template_version(body.clone_from_version_id)
        if source is None or source.template_id != template_id:
            raise NotFoundError("Source template version not found")
        spec = dict(source.spec_json)

    version = create_draft_version(template_id, spec, existing_versions)
    saved = repo.save_template_version(version)
    return TemplateVersionResponse(**asdict(saved))


@router.post("/template-families/{template_id}/versions/{version_id}/publish", response_model=TemplateVersionResponse)
def publish_template_version(
    template_id: str,
    version_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> TemplateVersionResponse:
    repo = IngestionRepository(db)
    version = repo.get_template_version(version_id)
    if version is None or version.template_id != template_id:
        raise NotFoundError("Template version not found")

    try:
        publish_version(version)
    except ValueError as e:
        raise ValidationError(str(e))

    updated = repo.update_version_state(version.id, version.state, version.published_at)
    if updated is None:
        raise NotFoundError("Template version not found")

    return TemplateVersionResponse(**asdict(updated))


@router.put("/templates/{pipeline_id}/bind", response_model=CleaningPipelineResponse)
def bind_pipeline_to_template(
    pipeline_id: str,
    body: BindTemplateRequest,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> CleaningPipelineResponse:
    repo = IngestionRepository(db)
    pipeline = repo.get_pipeline(pipeline_id)
    if pipeline is None:
        raise NotFoundError("Pipeline not found")

    version = repo.get_template_version(body.template_version_id)
    try:
        validate_bind(version)
    except ValueError as e:
        raise ValidationError(str(e))

    updated = repo.bind_upload_to_version(pipeline_id, body.template_version_id)
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


@router.post("/uploads/{upload_id}/process", response_model=ProcessUploadResponse)
def process_upload_endpoint(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> ProcessUploadResponse:
    repo = IngestionRepository(db)

    upload = repo.get_upload(upload_id)
    if upload is None:
        raise NotFoundError("Upload not found")

    pipeline = repo.get_pipeline_by_upload(upload_id)
    if pipeline is None or pipeline.template_version_id is None:
        raise ValidationError("No template version bound to this upload")

    version = repo.get_template_version(pipeline.template_version_id)
    if version is None or version.state != "published":
        raise ValidationError("No published template version found")

    steps = parse_spec_steps(version.spec_json)
    if not steps:
        raise ValidationError("Template version spec contains no steps")

    raw_rows = load_raw_rows(upload.storage_path)
    if not raw_rows:
        raise ValidationError("No raw data found for this upload")

    raw_columns = list(raw_rows[0].keys()) if raw_rows else []

    result = execute_cleaning_pipeline(raw_rows, steps)

    mapping_decisions = repo.get_mapping_decisions(upload_id)
    normalized = normalize_cleaned_rows(result.rows, mapping_decisions, result.rename_map)

    step_specs = version.spec_json.get("steps", [])
    graph = build_lineage_graph(
        upload_id=upload_id,
        file_name=upload.file_name,
        sheet_name="Sheet1",
        raw_columns=raw_columns,
        step_specs=step_specs,
        mapping_decisions=mapping_decisions,
        normalized_fields=normalized.field_map,
        rename_map=result.rename_map,
    )
    repo.save_lineage_graph(upload_id, graph)

    storage_path = save_cleaned_rows(normalized.rows, upload_id)

    all_warnings = list(result.warnings)
    all_warnings.extend(normalized.warnings)
    warning_count = len(all_warnings)

    cleaned_status = result.status
    if cleaned_status == CleanedSnapshotStatus.completed.value and normalized.warnings:
        cleaned_status = CleanedSnapshotStatus.completed_with_warnings.value

    snapshot = CleanedSnapshot(
        id=str(uuid.uuid4()),
        upload_id=upload_id,
        template_version_id=version.id,
        status=cleaned_status,
        row_count=result.row_count,
        warning_count=warning_count,
        warnings=all_warnings,
        storage_path=storage_path,
        created_at=datetime.now(UTC),
    )
    repo.save_cleaned_snapshot(snapshot)

    return ProcessUploadResponse(
        cleaned_snapshot_id=snapshot.id,
        status=snapshot.status,
        row_count=snapshot.row_count,
        warning_count=snapshot.warning_count,
        warnings=snapshot.warnings,
    )


@router.get("/uploads/{upload_id}/lineage", response_model=LineageGraphResponse)
def get_lineage_graph(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> LineageGraphResponse:
    repo = IngestionRepository(db)
    graph = repo.get_lineage_graph(upload_id)
    if graph is None:
        raise NotFoundError("No lineage graph found for this upload")
    return LineageGraphResponse(
        upload_id=upload_id,
        nodes=[{"id": n.id, "node_type": n.node_type.value, "label": n.label, "metadata": n.metadata} for n in graph.nodes],
        edges=[{"id": e.id, "from_node_id": e.from_node_id, "to_node_id": e.to_node_id, "edge_type": e.edge_type.value, "metadata": e.metadata} for e in graph.edges],
    )


@router.get("/uploads/{upload_id}/cleaned", response_model=CleanedSnapshotResponse)
def get_cleaned_snapshot(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
) -> CleanedSnapshotResponse:
    repo = IngestionRepository(db)
    snapshot = repo.get_cleaned_snapshot_by_upload(upload_id)
    if snapshot is None:
        raise NotFoundError("No cleaned snapshot found for this upload")

    return CleanedSnapshotResponse(
        id=snapshot.id,
        upload_id=snapshot.upload_id,
        template_version_id=snapshot.template_version_id,
        status=snapshot.status,
        row_count=snapshot.row_count,
        warning_count=snapshot.warning_count,
        warnings=snapshot.warnings,
        created_at=snapshot.created_at,
    )
