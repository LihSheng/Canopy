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
        state.status = IngestionWorkflowStatus.started
        state.current_step = "upload"
        state.error_message = None
        return self._repo.save_workflow_state(state)

    def after_profiling(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status == IngestionWorkflowStatus.mapped:
            return state
        if state.status == IngestionWorkflowStatus.failed:
            raise ValidationError("Workflow has failed")
        state.status = IngestionWorkflowStatus.profiled
        state.current_step = "profile"
        if "profile" not in state.completed_steps:
            state.completed_steps.append("profile")
        return self._repo.save_workflow_state(state)

    def after_mapping_saved(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        decisions = self._repo.get_mapping_decisions(upload_id)
        if not decisions:
            raise ValidationError("At least one mapping decision is required")
        if state.status == IngestionWorkflowStatus.failed:
            raise ValidationError("Workflow has failed")
        state.status = IngestionWorkflowStatus.mapped
        state.current_step = "mapping"
        if "mapping" not in state.completed_steps:
            state.completed_steps.append("mapping")
        return self._repo.save_workflow_state(state)

    def before_processing(self, upload_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status != IngestionWorkflowStatus.mapped:
            raise ValidationError("Mapping must be completed before processing")
        state.status = IngestionWorkflowStatus.processing
        state.current_step = "processing"
        if "processing" not in state.completed_steps:
            state.completed_steps.append("processing")
        return self._repo.save_workflow_state(state)

    def after_processing(self, upload_id: str, cleaned_snapshot_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        state.status = IngestionWorkflowStatus.processed
        state.cleaned_snapshot_id = cleaned_snapshot_id
        state.current_step = "processed"
        return self._repo.save_workflow_state(state)

    def after_publish(self, upload_id: str, publish_id: str) -> WorkflowState:
        state = self._require_state(upload_id)
        if state.status != IngestionWorkflowStatus.processed:
            raise ValidationError("Processing must complete before publish")
        state.status = IngestionWorkflowStatus.published
        state.publish_id = publish_id
        state.current_step = "published"
        return self._repo.save_workflow_state(state)

    def mark_failed(self, upload_id: str, message: str) -> WorkflowState | None:
        state = self._repo.get_state(upload_id)
        if state is None:
            return None
        state.status = IngestionWorkflowStatus.failed
        state.error_message = message
        state.current_step = "failed"
        return self._repo.save_workflow_state(state)

    def _require_state(self, upload_id: str) -> WorkflowState:
        state = self._repo.get_state(upload_id)
        if state is None:
            raise ValidationError("Upload not found")
        return state
