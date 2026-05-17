from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.ingestion import (
    MappingDecisionRequest,
    MappingDecisionResponse,
    MappingSuggestionsResponse,
    UploadResponse,
    WorkbookProfileResponse,
)
from common.database import get_db
from common.errors import ValidationError
from v3.ingestion.domain import MappingDecision
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
        from common.errors import NotFoundError
        raise NotFoundError("Upload not found")

    return UploadResponse(
        upload_id=record.id,
        status=record.status.value,
        file_name=record.file_name,
        file_size=record.file_size,
        checksum=record.checksum,
        created_at=record.created_at,
    )
