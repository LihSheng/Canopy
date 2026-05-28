from __future__ import annotations

from common.errors import ValidationError
from ingestion.domain import IngestionWorkflowStatus, WorkflowState
from ingestion.repository import IngestionRepository


class IngestionOrchestrator:
    def __init__(self, repo: IngestionRepository):
        self._repo = repo

    def get_state(self, upload_id: str) -> WorkflowState | None:
        return self._repo.get_state(upload_id)

    def after_upload(self, upload_id: str) -> WorkflowState:
        upload = self._repo.get_upload(upload_id)
        if upload is None:
            raise ValidationError("Upload not found")
        state = self._repo.get_state(upload_id) or WorkflowState(
            upload_id=upload_id, status=IngestionWorkflowStatus.started
        )
        state.error_message = None
        return self._transition(state, IngestionWorkflowStatus.started, "upload")

    def after_profiling(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status == IngestionWorkflowStatus.mapped:
            return state
        self._assert_not_failed(state)
        return self._transition(state, IngestionWorkflowStatus.profiled, "profile")

    def after_mapping_saved(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        decisions = self._repo.get_mapping_decisions(upload_id)
        if not decisions:
            raise ValidationError("At least one mapping decision is required")
        self._assert_not_failed(state)
        return self._transition(state, IngestionWorkflowStatus.mapped, "mapping")

    def before_processing(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status != IngestionWorkflowStatus.mapped:
            raise ValidationError("Mapping must be completed before processing")
        return self._transition(state, IngestionWorkflowStatus.processing, "processing")

    def after_processing(self, upload_id: str, cleaned_snapshot_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        state.cleaned_snapshot_id = cleaned_snapshot_id
        return self._transition(state, IngestionWorkflowStatus.processed, "processed")

    def after_publish(self, upload_id: str, publish_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status != IngestionWorkflowStatus.processed:
            raise ValidationError("Processing must complete before publish")
        state.publish_id = publish_id
        return self._transition(state, IngestionWorkflowStatus.published, "published")

    def mark_failed(self, upload_id: str, message: str) -> WorkflowState | None:
        state = self._repo.get_state(upload_id)
        if state is None:
            return None
        state.error_message = message
        return self._transition(state, IngestionWorkflowStatus.failed, "failed")

    def _require_state(self, upload_id: str) -> WorkflowState:
        state = self._repo.get_state(upload_id)
        if state is None:
            raise ValidationError("Upload not found")
        return state

    def _transition(self, state: WorkflowState, to_status: IngestionWorkflowStatus, step: str) -> WorkflowState:
        state.status = to_status
        state.current_step = step
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        return self._repo.save_workflow_state(state)

    @staticmethod
    def _assert_not_failed(state: WorkflowState) -> None:
        if state.status == IngestionWorkflowStatus.failed:
            raise ValidationError("Workflow has failed")
