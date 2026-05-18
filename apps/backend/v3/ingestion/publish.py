from __future__ import annotations

import uuid
from datetime import UTC, datetime

from v3.ingestion.domain import (
    CleanedSnapshot,
    MappingDecision,
    PublishRecord,
    PublishStatus,
    PublishValidationResult,
    TemplateVersion,
    UploadRecord,
)

_REQUIRED_FIELDS = {
    "payroll": {"employee", "amount", "date"},
    "claims": {"employee", "amount", "claim_type", "date"},
    "departments": {"name", "code"},
}


def validate_publish(
    upload_record: UploadRecord,
    mapping_decisions: list[MappingDecision],
    template_version: TemplateVersion,
    cleaned_snapshot: CleanedSnapshot,
) -> PublishValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if template_version.state != "published":
        errors.append("Template version must be published")
    if cleaned_snapshot.status == "failed":
        errors.append("Cleaned snapshot failed")
    elif cleaned_snapshot.status not in {"completed", "completed_with_warnings"}:
        errors.append(f"Unexpected status: {cleaned_snapshot.status}")
    if cleaned_snapshot.row_count <= 0:
        errors.append("Cleaned snapshot has zero rows")
    if cleaned_snapshot.warning_count and cleaned_snapshot.warning_count > 0:
        warnings.append(f"Cleaned snapshot has {cleaned_snapshot.warning_count} warnings")

    mapped_fields = {decision.target_field_name for decision in mapping_decisions if decision.confirmed}
    required = _REQUIRED_FIELDS.get(upload_record.dataset_type, set())
    missing = sorted(required - mapped_fields)
    if missing:
        errors.extend([f"Missing required field: {field}" for field in missing])

    return PublishValidationResult(valid=not errors, warnings=warnings, errors=errors)


def activate_publish(
    repo,
    upload_id: str,
    cleaned_snapshot_id: str,
    template_version_id: str,
    published_by: str | None = None,
) -> PublishRecord:
    if hasattr(repo, "deactivate_publish"):
        repo.deactivate_publish(upload_id)

    record = PublishRecord(
        id=str(uuid.uuid4()),
        upload_id=upload_id,
        cleaned_snapshot_id=cleaned_snapshot_id,
        template_version_id=template_version_id,
        status=PublishStatus.active.value,
        validation_errors=[],
        validation_warnings=[],
        published_at=datetime.now(UTC),
        published_by=published_by,
    )
    if hasattr(repo, "save_publish_record"):
        return repo.save_publish_record(record)
    return record
