import uuid
from datetime import UTC, datetime

from v3.ingestion.domain import (
    CleanedSnapshot,
    MappingDecision,
    PublishRecord,
    PublishValidationResult,
    TemplateVersion,
    UploadRecord,
)

_REQUIRED_FIELDS: dict[str, set[str]] = {
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

    required = _REQUIRED_FIELDS.get(upload_record.dataset_type)
    if required:
        mapped_fields = {md.target_field_name for md in mapping_decisions if md.confirmed}
        missing = required - mapped_fields
        if missing:
            errors.append(f"Required fields missing from mapping: {', '.join(sorted(missing))}")

    if template_version.state != "published":
        errors.append("Template version must be in 'published' state")

    if cleaned_snapshot.status == "failed":
        errors.append("Cannot publish a failed cleaned snapshot")
    elif cleaned_snapshot.status not in ("completed", "completed_with_warnings"):
        errors.append(f"Cleaned snapshot has unexpected status: {cleaned_snapshot.status}")

    if cleaned_snapshot.row_count == 0:
        errors.append("Cleaned snapshot has zero rows")

    if cleaned_snapshot.warning_count > 0:
        warnings.append(f"Cleaned snapshot has {cleaned_snapshot.warning_count} warnings")

    return PublishValidationResult(
        valid=len(errors) == 0,
        warnings=warnings,
        errors=errors,
    )


def activate_publish(
    repo,
    upload_id: str,
    cleaned_snapshot_id: str,
    template_version_id: str,
    published_by: str | None = None,
    validation_errors: list[str] | None = None,
    validation_warnings: list[str] | None = None,
) -> PublishRecord:
    repo.deactivate_publish(upload_id)

    now = datetime.now(UTC)
    record = PublishRecord(
        id=str(uuid.uuid4()),
        upload_id=upload_id,
        cleaned_snapshot_id=cleaned_snapshot_id,
        template_version_id=template_version_id,
        status="active",
        published_at=now,
        published_by=published_by,
        validation_errors=validation_errors or [],
        validation_warnings=validation_warnings or [],
        created_at=now,
    )
    return repo.save_publish_record(record)
