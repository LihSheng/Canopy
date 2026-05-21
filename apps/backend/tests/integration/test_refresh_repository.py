from common.clock import utcnow
from refresh.domain import RefreshJob
from refresh.repository import RefreshRepository

_SNAPSHOT_ID = "test-snapshot-001"


class TestRefreshRepository:
    def test_save_job_and_get_job(self, db_session):
        repo = RefreshRepository(db_session)
        job = RefreshJob(id="job-1", status="pending")
        repo.save_job(job)

        found = repo.get_job("job-1")
        assert found is not None
        assert found.id == "job-1"
        assert found.status == "pending"

    def test_save_job_with_all_fields(self, db_session):
        repo = RefreshRepository(db_session)
        job = RefreshJob(
            id="job-full",
            status="running",
            current_stage="extract_source",
            snapshot_id=_SNAPSHOT_ID,
            trigger_type="manual",
            requested_by_user_id="user-1",
            started_at=utcnow(),
        )
        repo.save_job(job)

        found = repo.get_job("job-full")
        assert found is not None
        assert found.current_stage == "extract_source"
        assert found.trigger_type == "manual"
        assert found.started_at is not None

    def test_get_job_returns_none(self, db_session):
        repo = RefreshRepository(db_session)
        assert repo.get_job("nonexistent") is None

    def test_update_job(self, db_session):
        repo = RefreshRepository(db_session)
        job = RefreshJob(id="job-update", status="pending")
        repo.save_job(job)

        job.status = "running"
        job.current_stage = "normalize_ontology"
        job.snapshot_id = _SNAPSHOT_ID
        repo.update_job(job)

        found = repo.get_job("job-update")
        assert found is not None
        assert found.status == "running"
        assert found.current_stage == "normalize_ontology"

    def test_update_job_raises_on_missing(self, db_session):
        import pytest

        repo = RefreshRepository(db_session)
        job = RefreshJob(id="missing", status="pending")
        with pytest.raises(ValueError, match="not found"):
            repo.update_job(job)

    def test_mark_current_snapshot(self, db_session):
        repo = RefreshRepository(db_session)
        job = RefreshJob(id="job-snap", status="completed")
        repo.save_job(job)

        repo.mark_current_snapshot(job_id="job-snap", snapshot_id=_SNAPSHOT_ID)

        current = repo.get_current_snapshot()
        assert current is not None
        assert current.status == "current"
        assert current.id == _SNAPSHOT_ID

    def test_get_current_snapshot_returns_none_when_empty(self, db_session):
        repo = RefreshRepository(db_session)
        assert repo.get_current_snapshot() is None

    def test_mark_current_snapshot_archives_old(self, db_session):
        repo = RefreshRepository(db_session)
        job = RefreshJob(id="job-snap-2", status="completed")
        repo.save_job(job)

        repo.mark_current_snapshot(job_id="job-snap-2", snapshot_id="snap-v1")
        repo.mark_current_snapshot(job_id="job-snap-2", snapshot_id="snap-v2")

        current = repo.get_current_snapshot()
        assert current is not None
        assert current.id == "snap-v2"

        old = repo.get_current_snapshot()
        assert old.id == "snap-v2"

    def test_get_latest_job_returns_most_recent(self, db_session):
        repo = RefreshRepository(db_session)
        from datetime import UTC, datetime

        job1 = RefreshJob(id="job-old", status="completed", started_at=datetime(2026, 1, 1, tzinfo=UTC))
        job2 = RefreshJob(id="job-new", status="running", started_at=datetime(2026, 5, 1, tzinfo=UTC))
        repo.save_job(job1)
        repo.save_job(job2)

        latest = repo.get_latest_job()
        assert latest is not None
        assert latest.id == "job-new"

    def test_get_latest_job_returns_none_when_empty(self, db_session):
        repo = RefreshRepository(db_session)
        assert repo.get_latest_job() is None
