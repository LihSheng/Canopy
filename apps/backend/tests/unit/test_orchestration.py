import pytest
from sqlalchemy.orm import Session

from common.errors import ValidationError
from ingestion.domain import (
    IngestionWorkflowStatus,
    MappingDecision,
    UploadRecord,
    UploadStatus,
    WorkflowState,
)
from ingestion.orchestration import IngestionOrchestrator
from ingestion.repository import IngestionRepository


class TestWorkflowInitialization:
    def test_init_after_upload_creates_started_state(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)

        state = orch.after_upload(upload.id)

        assert state.status == IngestionWorkflowStatus.started
        assert state.completed_steps == []
        assert state.current_step == "upload"
        assert state.error_message is None

    def test_init_is_idempotent(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)

        state1 = orch.after_upload(upload.id)
        state2 = orch.after_upload(upload.id)

        assert state1.status == state2.status
        assert state1.upload_id == state2.upload_id

    def test_get_state_returns_none_for_missing_upload(self, db_session: Session):
        repo = IngestionRepository(db_session)
        orch = IngestionOrchestrator(repo)

        state = orch.get_state("nonexistent")
        assert state is None


class TestStateTransitions:
    def test_full_flow_transitions(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)

        orch.after_upload(upload.id)
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.started

        orch.after_profiling(upload.id)
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.profiled

        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.mapped

        orch.before_processing(upload.id)
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.processing

        orch.after_processing(upload.id, "snapshot-1")
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.processed
        assert orch.get_state(upload.id).cleaned_snapshot_id == "snapshot-1"

        orch.after_publish(upload.id, "publish-1")
        assert orch.get_state(upload.id).status == IngestionWorkflowStatus.published
        assert orch.get_state(upload.id).publish_id == "publish-1"

    def test_transition_started_to_profiled(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        state = orch.after_profiling(upload.id)

        assert state.status == IngestionWorkflowStatus.profiled
        assert "profile" in state.completed_steps

    def test_transition_profiled_to_mapped(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)

        state = orch.after_mapping_saved(upload.id)

        assert state.status == IngestionWorkflowStatus.mapped
        assert "mapping" in state.completed_steps

    def test_transition_mapped_to_processing(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)

        state = orch.before_processing(upload.id)

        assert state.status == IngestionWorkflowStatus.processing
        assert "processing" in state.completed_steps

    def test_transition_processing_to_processed(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)
        orch.before_processing(upload.id)

        state = orch.after_processing(upload.id, "snapshot-1")

        assert state.status == IngestionWorkflowStatus.processed
        assert state.cleaned_snapshot_id == "snapshot-1"

    def test_transition_processed_to_published(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)
        orch.before_processing(upload.id)
        orch.after_processing(upload.id, "snapshot-1")

        state = orch.after_publish(upload.id, "publish-1")

        assert state.status == IngestionWorkflowStatus.published
        assert state.publish_id == "publish-1"

    def test_completed_steps_accumulate(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)

        state = orch.get_state(upload.id)
        assert "profile" in state.completed_steps
        assert "mapping" in state.completed_steps


class TestOutOfOrderTransitions:
    def test_cannot_process_before_mapping(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)

        with pytest.raises(ValidationError):
            orch.before_processing(upload.id)

    def test_cannot_process_from_started(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        with pytest.raises(ValidationError):
            orch.before_processing(upload.id)

    def test_cannot_publish_before_processing(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)

        with pytest.raises(ValidationError):
            orch.after_publish(upload.id, "publish-1")

    def test_profil_after_mapped_is_noop(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)

        state = orch.after_profiling(upload.id)
        assert state.status == IngestionWorkflowStatus.mapped

    def test_mapping_works_from_started(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        _seed_mappings(repo, upload.id)
        state = orch.after_mapping_saved(upload.id)
        assert state.status == IngestionWorkflowStatus.mapped

    def test_cannot_profile_before_upload(self, db_session: Session):
        repo = IngestionRepository(db_session)
        orch = IngestionOrchestrator(repo)

        with pytest.raises(ValidationError):
            orch.after_profiling("nonexistent")


class TestFailedState:
    def test_mark_failed_from_started(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        result = orch.mark_failed(upload.id, "Something went wrong")

        assert result is not None
        assert result.status == IngestionWorkflowStatus.failed
        assert result.error_message == "Something went wrong"

    def test_mark_failed_from_any_state(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)
        _seed_mappings(repo, upload.id)
        orch.after_mapping_saved(upload.id)

        result = orch.mark_failed(upload.id, "Processing error")

        assert result.status == IngestionWorkflowStatus.failed
        assert result.error_message == "Processing error"

    def test_cannot_transition_from_failed(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.mark_failed(upload.id, "Error")

        with pytest.raises(ValidationError):
            orch.after_profiling(upload.id)

    def test_mark_failed_nonexistent_upload_returns_none(self, db_session: Session):
        repo = IngestionRepository(db_session)
        orch = IngestionOrchestrator(repo)

        result = orch.mark_failed("nonexistent", "Error")
        assert result is None


class TestValidationChecks:
    def test_mapping_requires_decisions(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)
        orch.after_profiling(upload.id)

        with pytest.raises(ValidationError, match="At least one mapping decision"):
            orch.after_mapping_saved(upload.id)

    def test_get_state_returns_correct_state(self, db_session: Session):
        repo = IngestionRepository(db_session)
        upload = _seed_upload(repo)
        orch = IngestionOrchestrator(repo)
        orch.after_upload(upload.id)

        state = orch.get_state(upload.id)
        assert state.upload_id == upload.id
        assert state.status == IngestionWorkflowStatus.started


def _seed_upload(repo: IngestionRepository) -> UploadRecord:
    record = UploadRecord(
        id="test-upload-orch-1",
        file_name="test.csv",
        file_size=100,
        mime_type="text/csv",
        storage_path="/tmp/test.csv",
        checksum="abc123",
        status=UploadStatus.uploaded,
        source_profile="herdhr",
        dataset_type="payroll",
    )
    return repo.save_upload(record)


def _seed_mappings(repo: IngestionRepository, upload_id: str) -> None:
    decisions = [
        MappingDecision(
            source_column_name="name",
            target_field_name="employee_name",
            confirmed=True,
            overridden_by_user=False,
        ),
    ]
    repo.save_mapping_decisions(upload_id, decisions)

