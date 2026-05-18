from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from common.config import settings
from common.errors import ValidationError
from v3.ingestion.domain import UploadRecord, UploadStatus

_ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".csv"}
_MAX_FILE_SIZE = 50 * 1024 * 1024
_MIME_TYPES = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".csv": "text/csv",
}


def _get_upload_dir() -> Path:
    if settings.export_storage_dir:
        base = Path(settings.export_storage_dir)
    else:
        base = Path(__file__).resolve().parents[2] / "storage"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _compute_checksum(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


def process_upload(
    repo,
    file_bytes: bytes,
    file_name: str,
    source_profile: str,
    dataset_type: str,
) -> UploadRecord:
    suffix = Path(file_name).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise ValidationError("Unsupported file type")
    if len(file_bytes) > _MAX_FILE_SIZE:
        raise ValidationError("File exceeds maximum size")

    upload_dir = _get_upload_dir()
    upload_id = str(uuid.uuid4())
    storage_path = upload_dir / f"{upload_id}{suffix}"
    storage_path.write_bytes(file_bytes)

    record = UploadRecord(
        id=upload_id,
        file_name=file_name,
        file_size=len(file_bytes),
        mime_type=_MIME_TYPES[suffix],
        storage_path=str(storage_path),
        checksum=_compute_checksum(file_bytes),
        status=UploadStatus.uploaded,
        source_profile=source_profile,
        dataset_type=dataset_type,
    )
    return repo.save_upload(record)
