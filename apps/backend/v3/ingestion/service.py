import hashlib
import os
import uuid
from pathlib import Path

from common.config import settings
from common.errors import ValidationError
from v3.ingestion.domain import UploadRecord, UploadStatus
from v3.ingestion.repository import IngestionRepository


def _get_upload_dir() -> Path:
    base = Path(settings.export_storage_dir or Path.home() / ".herd-aggregator")
    upload_dir = base / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _compute_checksum(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


_ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".xlsm", ".csv"}
_MAX_FILE_SIZE = 50 * 1024 * 1024
_MIME_TYPES: dict[str, str] = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
    ".xlsm": "application/vnd.ms-excel.sheet.macroEnabled.12",
    ".csv": "text/csv",
}


def process_upload(repo: IngestionRepository, file_bytes: bytes, file_name: str, source_profile: str, dataset_type: str) -> UploadRecord:
    ext = Path(file_name).suffix.lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValidationError(f"Unsupported file type '{ext}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}")

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise ValidationError(f"File exceeds maximum size of {_MAX_FILE_SIZE // (1024*1024)} MB")

    mime_type = _MIME_TYPES.get(ext, "application/octet-stream")

    upload_id = str(uuid.uuid4())
    upload_dir = _get_upload_dir()
    storage_name = f"{upload_id}{ext}"
    storage_path = upload_dir / storage_name

    storage_path.write_bytes(file_bytes)

    checksum = _compute_checksum(storage_path)

    record = UploadRecord(
        id=upload_id,
        file_name=file_name,
        file_size=len(file_bytes),
        mime_type=mime_type,
        storage_path=str(storage_path),
        checksum=checksum,
        status=UploadStatus.uploaded,
        source_profile=source_profile,
        dataset_type=dataset_type,
    )

    return repo.save_upload(record)
