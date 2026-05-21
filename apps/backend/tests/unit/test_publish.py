import uuid

import pytest

from ingestion.domain import (
    CleanedSnapshot,
    MappingDecision,
    PublishRecord,
    PublishStatus,
    TemplateVersion,
    UploadRecord,
    UploadStatus,
)
from ingestion.publish import activate_publish, validate_publish

pytestmark = pytest.mark.business_rule


def _make_upload(dataset_type: str = "payroll") -> UploadRecord:
    return UploadRecord(
        id=str(uuid.uuid4()),
        file_name="test.csv",
        file_size=100,
        mime_type="text/csv",
        storage_path="/tmp/test.csv",
        checksum="abc123",
        status=UploadStatus.uploaded,
        source_profile="herdhr",
        dataset_type=dataset_type,
    )


def _make_mapping_decisions(*fields: str) -> list[MappingDecision]:
    return [
        MappingDecision(
            source_column_name=f"col_{i}",
            target_field_name=f,
            confirmed=True,
            overridden_by_user=False,
        )
        for i, f in enumerate(fields)
    ]


def _make_template_version(state: str = "published") -> TemplateVersion:
    return TemplateVersion(
        id=str(uuid.uuid4()),
        template_id=str(uuid.uuid4()),
        version_number=1,
        state=state,
        spec_json={},
    )


def _make_snapshot(status: str = "completed", row_count: int = 10, warning_count: int = 0) -> CleanedSnapshot:
    return CleanedSnapshot(
        id=str(uuid.uuid4()),
        upload_id=str(uuid.uuid4()),
        template_version_id=str(uuid.uuid4()),
        status=status,
        row_count=row_count,
        warning_count=warning_count,
        warnings=[],
        storage_path="/tmp/cleaned.json",
    )


class FakeRepo:
    def __init__(self):
        self.records: list[PublishRecord] = []

    def deactivate_publish(self, upload_id: str) -> None:
        for r in self.records:
            if r.upload_id == upload_id and r.status == "active":
                r.status = PublishStatus.revoked.value

    def save_publish_record(self, record: PublishRecord) -> PublishRecord:
        self.records.append(record)
        return record

    def get_active_publish(self, upload_id: str) -> PublishRecord | None:
        for r in self.records:
            if r.upload_id == upload_id and r.status == "active":
                return r
        return None

    def list_publish_history(self, upload_id: str) -> list[PublishRecord]:
        return sorted(
            [r for r in self.records if r.upload_id == upload_id],
            key=lambda r: r.created_at,
            reverse=True,
        )

    def get_publish_record(self, publish_id: str) -> PublishRecord | None:
        for r in self.records:
            if r.id == publish_id:
                return r
        return None


class TestValidatePublish:
    def test_validate_passes_with_complete_state(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_validate_passes_with_completed_with_warnings(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed_with_warnings", 10, 3)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is True
        assert result.errors == []
        assert len(result.warnings) == 1
        assert "3 warnings" in result.warnings[0]

    def test_validate_fails_when_required_mapping_missing(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("amount" in e for e in result.errors)
        assert any("date" in e for e in result.errors)

    def test_validate_fails_when_template_is_draft(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("draft")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("published" in e.lower() for e in result.errors)

    def test_validate_fails_when_cleaned_snapshot_is_failed(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("failed", 0, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("failed" in e.lower() for e in result.errors)

    def test_validate_fails_when_snapshot_has_zero_rows(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 0, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("zero rows" in e.lower() for e in result.errors)

    def test_validate_claims_required_fields(self):
        upload = _make_upload("claims")
        mappings = _make_mapping_decisions("employee", "amount", "claim_type", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is True

    def test_validate_claims_missing_claim_type(self):
        upload = _make_upload("claims")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("claim_type" in e for e in result.errors)

    def test_validate_departments_required_fields(self):
        upload = _make_upload("departments")
        mappings = _make_mapping_decisions("name", "code")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 5, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is True

    def test_validate_departments_missing_name(self):
        upload = _make_upload("departments")
        mappings = _make_mapping_decisions("code")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 5, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("name" in e for e in result.errors)

    def test_validate_unknown_dataset_type_no_required_check(self):
        upload = _make_upload("unknown_type")
        mappings = _make_mapping_decisions("anything")
        version = _make_template_version("published")
        snapshot = _make_snapshot("completed", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is True

    def test_validate_snapshot_unexpected_status(self):
        upload = _make_upload("payroll")
        mappings = _make_mapping_decisions("employee", "amount", "date")
        version = _make_template_version("published")
        snapshot = _make_snapshot("unknown_status", 10, 0)

        result = validate_publish(upload, mappings, version, snapshot)
        assert result.valid is False
        assert any("unexpected status" in e.lower() for e in result.errors)


class TestActivatePublish:
    def test_activate_creates_active_record(self):
        repo = FakeRepo()
        upload_id = str(uuid.uuid4())
        snapshot_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())

        record = activate_publish(repo, upload_id, snapshot_id, version_id)
        assert record.status == "active"
        assert record.upload_id == upload_id
        assert record.cleaned_snapshot_id == snapshot_id
        assert record.template_version_id == version_id
        assert record.published_at is not None

    def test_activate_saves_to_repo(self):
        repo = FakeRepo()
        record = activate_publish(repo, "upload-1", "snap-1", "ver-1")
        assert len(repo.records) == 1
        assert repo.records[0].id == record.id

    def test_republish_deactivates_old_creates_new(self):
        repo = FakeRepo()
        record1 = activate_publish(repo, "upload-1", "snap-1", "ver-1")
        assert record1.status == "active"

        record2 = activate_publish(repo, "upload-1", "snap-2", "ver-2")
        assert record2.status == "active"
        assert record2.cleaned_snapshot_id == "snap-2"

        active = repo.get_active_publish("upload-1")
        assert active is not None
        assert active.id == record2.id

        old = repo.get_publish_record(record1.id)
        assert old is not None
        assert old.status == "revoked"

    def test_activate_with_published_by(self):
        repo = FakeRepo()
        record = activate_publish(repo, "upload-1", "snap-1", "ver-1", published_by="user-1")
        assert record.published_by == "user-1"

    def test_list_history_returns_all(self):
        repo = FakeRepo()
        activate_publish(repo, "upload-1", "snap-1", "ver-1")
        activate_publish(repo, "upload-1", "snap-2", "ver-2")

        history = repo.list_publish_history("upload-1")
        assert len(history) == 2

    def test_history_ordered_newest_first(self):
        import time

        repo = FakeRepo()
        r1 = activate_publish(repo, "upload-1", "snap-1", "ver-1")
        time.sleep(0.01)
        r2 = activate_publish(repo, "upload-1", "snap-2", "ver-2")

        history = repo.list_publish_history("upload-1")
        assert history[0].id == r2.id
        assert history[1].id == r1.id

    def test_deactivate_publish_none_active(self):
        repo = FakeRepo()
        repo.deactivate_publish("nonexistent")
        assert len(repo.records) == 0
