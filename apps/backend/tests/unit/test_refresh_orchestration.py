import uuid
from unittest.mock import MagicMock, patch

import pytest

from common.errors import AppError
from refresh.domain import RefreshJob, STAGE_ORDER
from refresh.orchestration.service import RefreshOrchestrator


def _make_job(status: str = "pending") -> RefreshJob:
    return RefreshJob(
        id=str(uuid.uuid4()),
        status=status,
        trigger_type="manual",
        requested_by_user_id="user-1",
    )


def _make_sync_result(snapshot_id="snap-001", status="completed"):
    fake_snap = MagicMock()
    fake_snap.entity_type = "departments"
    fake_snap.status = "completed"
    fake_snap.rows = [MagicMock()]
    result = MagicMock()
    result.snapshot_id = snapshot_id
    result.status = status
    result.snapshots = [fake_snap]
    result.error_message = None
    return result


class TestRefreshStatusTransitions:
    def test_status_transitions_pending_to_completed(self):
        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_result = _make_sync_result()
        mock_sync_orch.run.return_value = mock_sync_result

        mock_onto_orch = MagicMock()

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
            patch(
                "refresh.orchestration.service.OntologyOrchestrator",
                return_value=mock_onto_orch,
            ),
            patch(
                "refresh.orchestration.service.run_aggregation_pipeline",
            ),
            patch(
                "refresh.orchestration.service.detect_anomalies",
            ),
            patch(
                "refresh.orchestration.service.generate_insight",
            ),
            patch.object(
                RefreshOrchestrator,
                "_resolve_months",
                return_value=("2026-05", "2026-04"),
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            result = orchestrator.run(job)

            assert result.status == "completed"
            assert result.started_at is not None
            assert result.finished_at is not None

    def test_all_stages_run_in_order(self):
        call_order = []
        mock_sync_result = _make_sync_result()

        def make_extract_result(fn):
            def wrapped(*args, **kwargs):
                call_order.append("extract_source")
                return mock_sync_result
            return wrapped

        def make_stage_fn(name, result=None):
            def fn(*args, **kwargs):
                call_order.append(name)
                return result

            return fn

        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_orch.run.side_effect = make_extract_result(mock_sync_orch.run)

        mock_onto_orch = MagicMock()
        mock_onto_orch.map_all.side_effect = make_stage_fn("normalize_ontology")

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
            patch(
                "refresh.orchestration.service.OntologyOrchestrator",
                return_value=mock_onto_orch,
            ),
            patch(
                "refresh.orchestration.service.run_aggregation_pipeline",
                side_effect=make_stage_fn("rebuild_aggregates"),
            ),
            patch(
                "refresh.orchestration.service.detect_anomalies",
                side_effect=make_stage_fn("detect_anomalies", result=[]),
            ),
            patch(
                "refresh.orchestration.service.generate_insight",
                side_effect=make_stage_fn("generate_insights"),
            ),
            patch.object(
                RefreshOrchestrator,
                "_publish_snapshot",
                side_effect=make_stage_fn("publish_snapshot"),
            ),
            patch.object(
                RefreshOrchestrator,
                "_resolve_months",
                return_value=("2026-05", "2026-04"),
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            orchestrator.run(job)

        expected = [
            "extract_source",
            "normalize_ontology",
            "rebuild_aggregates",
            "detect_anomalies",
            "generate_insights",
            "publish_snapshot",
        ]
        assert call_order == expected


class TestPublishGating:
    def test_completed_job_publishes_snapshot_as_current(self):
        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_result = _make_sync_result(snapshot_id="snap-001")
        mock_sync_orch.run.return_value = mock_sync_result

        mock_onto_orch = MagicMock()

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
            patch(
                "refresh.orchestration.service.OntologyOrchestrator",
                return_value=mock_onto_orch,
            ),
            patch(
                "refresh.orchestration.service.run_aggregation_pipeline",
            ),
            patch(
                "refresh.orchestration.service.detect_anomalies",
            ),
            patch(
                "refresh.orchestration.service.generate_insight",
            ),
            patch.object(
                RefreshOrchestrator,
                "_resolve_months",
                return_value=("2026-05", "2026-04"),
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            orchestrator.run(job)

            assert job.status == "completed"
            assert job.snapshot_id == "snap-001"

    def test_failed_sync_does_not_publish_snapshot(self):
        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_result = _make_sync_result(status="failed")
        mock_sync_result.error_message = "Connection refused"
        mock_sync_orch.run.return_value = mock_sync_result

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            result = orchestrator.run(job)

            assert result.status == "failed"
            assert "Connection refused" in (result.error_message or "")


class TestFailureHandling:
    def test_mid_pipeline_failure_preserves_error_on_job(self):
        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_result = _make_sync_result()
        mock_sync_orch.run.return_value = mock_sync_result

        mock_onto_orch = MagicMock()

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
            patch(
                "refresh.orchestration.service.OntologyOrchestrator",
                return_value=mock_onto_orch,
            ),
            patch(
                "refresh.orchestration.service.run_aggregation_pipeline",
                side_effect=RuntimeError("DB timeout"),
            ),
            patch.object(
                RefreshOrchestrator,
                "_resolve_months",
                return_value=("2026-05", "2026-04"),
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            result = orchestrator.run(job)

            assert result.status == "failed"
            assert result.finished_at is not None
            assert "rebuild_aggregates" in (result.error_message or "")
            assert "DB timeout" in (result.error_message or "")

    def test_failure_sets_current_stage_to_failed_stage(self):
        job = _make_job(status="pending")
        app_db = MagicMock()
        source_db = MagicMock()

        mock_sync_orch = MagicMock()
        mock_sync_result = _make_sync_result()
        mock_sync_orch.run.return_value = mock_sync_result

        mock_onto_orch = MagicMock()
        mock_onto_orch.map_all.side_effect = ValueError("Invalid mapping")

        with (
            patch(
                "refresh.orchestration.service.SyncOrchestrator",
                return_value=mock_sync_orch,
            ),
            patch(
                "refresh.orchestration.service.OntologyOrchestrator",
                return_value=mock_onto_orch,
            ),
        ):
            orchestrator = RefreshOrchestrator(app_db=app_db, source_db=source_db)
            result = orchestrator.run(job)

            assert result.status == "failed"
            assert "normalize_ontology" in (result.error_message or "")

    def test_stage_order_enum_is_correct(self):
        assert STAGE_ORDER == [
            "extract_source",
            "normalize_ontology",
            "rebuild_aggregates",
            "detect_anomalies",
            "generate_insights",
            "publish_snapshot",
        ]

    def test_previous_month_computation(self):
        orchestrator = RefreshOrchestrator(
            app_db=MagicMock(), source_db=MagicMock()
        )
        assert orchestrator._previous_month("2026-05") == "2026-04"
        assert orchestrator._previous_month("2026-01") == "2025-12"
        assert orchestrator._previous_month("2025-12") == "2025-11"

    def test_initial_empty_job_is_pending(self):
        job = _make_job(status="pending")
        assert job.id is not None
        assert job.status == "pending"
        assert job.snapshot_id is None
        assert job.error_message is None
        assert job.started_at is None
        assert job.finished_at is None
