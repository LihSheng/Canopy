from common.errors import ValidationError
from v3.ingestion.domain import IngestionWorkflowStatus, WorkflowState
from v3.ingestion.repository import IngestionRepository


class IngestionOrchestrator:
    def __init__(self, repo: IngestionRepository):
        self._repo = repo

    def after_upload(self, upload_id: str) -> WorkflowState:
        return self._repo.init_workflow(upload_id)

    def after_profiling(self, upload_id: str) -> WorkflowState:
        state = self._get_or_raise(upload_id)
        if state.status != IngestionWorkflowStatus.started:
            return state
        return self._repo.update_workflow_step(
            upload_id, IngestionWorkflowStatus.profiled, "profile"
        )

    def after_mapping_saved(self, upload_id: str) -> WorkflowState:
        state = self._get_or_raise(upload_id)
        if state.status in (
            IngestionWorkflowStatus.mapped,
            IngestionWorkflowStatus.processing,
            IngestionWorkflowStatus.processed,
            IngestionWorkflowStatus.published,
        ):
            return state
        if state.status not in (IngestionWorkflowStatus.started, IngestionWorkflowStatus.profiled):
            raise ValidationError(f"Cannot transition from '{state.status.value}'")
        decisions = self._repo.get_mapping_decisions(upload_id)
        if not decisions:
            raise ValidationError("At least one mapping decision is required")
        return self._repo.update_workflow_step(
            upload_id, IngestionWorkflowStatus.mapped, "mapping"
        )

    def before_processing(self, upload_id: str) -> WorkflowState:
        state = self._get_or_raise(upload_id)
        if state.status in (
            IngestionWorkflowStatus.processing,
            IngestionWorkflowStatus.processed,
            IngestionWorkflowStatus.published,
        ):
            return state
        if state.status != IngestionWorkflowStatus.mapped:
            raise ValidationError(
                f"Cannot transition from '{state.status.value}' to 'processing'; "
                f"expected state 'mapped'"
            )
        return self._repo.update_workflow_step(
            upload_id, IngestionWorkflowStatus.processing, "processing"
        )

    def after_processing(self, upload_id: str, cleaned_snapshot_id: str) -> WorkflowState:
        state = self._get_or_raise(upload_id)
        if state.status in (IngestionWorkflowStatus.processed, IngestionWorkflowStatus.published):
            return state
        if state.status != IngestionWorkflowStatus.processing:
            raise ValidationError(
                f"Cannot transition from '{state.status.value}' to 'processed'; "
                f"expected state 'processing'"
            )
        return self._repo.update_workflow_step(
            upload_id, IngestionWorkflowStatus.processed, None,
            cleaned_snapshot_id=cleaned_snapshot_id,
        )

    def after_publish(self, upload_id: str, publish_id: str) -> WorkflowState:
        state = self._get_or_raise(upload_id)
        if state.status == IngestionWorkflowStatus.published:
            return state
        if state.status != IngestionWorkflowStatus.processed:
            raise ValidationError(
                f"Cannot transition from '{state.status.value}' to 'published'; "
                f"expected state 'processed'"
            )
        return self._repo.update_workflow_step(
            upload_id, IngestionWorkflowStatus.published, "publish",
            publish_id=publish_id,
        )

    def mark_failed(self, upload_id: str, error: str) -> WorkflowState | None:
        try:
            return self._repo.update_workflow_step(
                upload_id, IngestionWorkflowStatus.failed, None,
                error_message=error,
            )
        except Exception:
            return None

    def get_state(self, upload_id: str) -> WorkflowState | None:
        return self._repo.get_workflow_state(upload_id)

    def _get_or_raise(self, upload_id: str) -> WorkflowState:
        state = self._repo.get_workflow_state(upload_id)
        if state is None:
            raise ValidationError(f"Workflow not initialized for upload '{upload_id}'")
        if state.status == IngestionWorkflowStatus.failed:
            raise ValidationError(
                f"Workflow is in 'failed' state: {state.error_message or 'Unknown error'}"
            )
        return state
