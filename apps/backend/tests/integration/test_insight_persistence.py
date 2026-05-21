import pytest

from insights.domain import InsightSummary
from insights.repository import InsightRepository

_T = "2026-05-15T10:00:00+00:00"


class TestInsightPersistence:
    def test_save_and_find_latest(self, db_session):
        repo = InsightRepository(db_session)
        summary = InsightSummary(
            id="insight-1",
            snapshot_id="snap-1",
            current_month="2026-05",
            summary_text="Stable spend.",
            recommendations=["R1", "R2"],
            key_findings=["F1", "F2"],
            is_fallback=False,
            generated_at="2026-05-15T10:00:00+00:00",
            anomaly_count=2,
            department_count=6,
            total_payroll=1490500.0,
            total_claims=13770.0,
        )
        repo.save(summary)

        result = repo.find_latest()

        assert result is not None
        assert result.id == "insight-1"
        assert result.summary_text == "Stable spend."
        assert result.recommendations == ["R1", "R2"]
        assert result.key_findings == ["F1", "F2"]
        assert result.is_fallback is False
        assert result.anomaly_count == 2
        assert result.department_count == 6

    def test_find_by_snapshot(self, db_session):
        repo = InsightRepository(db_session)
        repo.save(
            InsightSummary(
                id="i-1",
                snapshot_id="snap-a",
                current_month="2026-05",
                summary_text="A",
                generated_at="2026-05-15T10:00:00+00:00",
            )
        )
        repo.save(
            InsightSummary(
                id="i-2",
                snapshot_id="snap-b",
                current_month="2026-05",
                summary_text="B",
                generated_at="2026-05-15T11:00:00+00:00",
            )
        )

        result = repo.find_by_snapshot("snap-a")

        assert result is not None
        assert result.id == "i-1"

    def test_find_by_month(self, db_session):
        repo = InsightRepository(db_session)
        repo.save(
            InsightSummary(
                id="i-1",
                snapshot_id="snap-1",
                current_month="2026-04",
                summary_text="A",
                generated_at="2026-04-15T10:00:00+00:00",
            )
        )
        repo.save(
            InsightSummary(
                id="i-2",
                snapshot_id="snap-2",
                current_month="2026-05",
                summary_text="B",
                generated_at="2026-05-15T10:00:00+00:00",
            )
        )

        result = repo.find_by_month("2026-05")

        assert result is not None
        assert result.id == "i-2"

    def test_clear_snapshot(self, db_session):
        repo = InsightRepository(db_session)
        repo.save(
            InsightSummary(
                id="i-1",
                snapshot_id="snap-x",
                current_month="2026-05",
                summary_text="X",
                generated_at="2026-05-15T10:00:00+00:00",
            )
        )

        repo.clear_snapshot("snap-x")
        result = repo.find_latest()

        assert result is None

    def test_find_latest_returns_none_when_empty(self, db_session):
        repo = InsightRepository(db_session)
        result = repo.find_latest()

        assert result is None

    def test_fallback_flag_persisted(self, db_session):
        repo = InsightRepository(db_session)
        repo.save(
            InsightSummary(
                id="i-fb",
                snapshot_id="snap-1",
                current_month="2026-05",
                summary_text="Fallback",
                is_fallback=True,
                generated_at="2026-05-15T10:00:00+00:00",
            )
        )

        result = repo.find_latest()

        assert result is not None
        assert result.is_fallback is True

    def test_snapshot_alignment(self, db_session):
        """Verify insight is tied to the same snapshot used for generation."""
        repo = InsightRepository(db_session)
        summary = InsightSummary(
            id="i-snap",
            snapshot_id="aligned-snap-001",
            current_month="2026-05",
            summary_text="Aligned",
            generated_at="2026-05-15T10:00:00+00:00",
        )
        repo.save(summary)

        result = repo.find_by_snapshot("aligned-snap-001")

        assert result is not None
        assert result.snapshot_id == "aligned-snap-001"
        assert result.current_month == "2026-05"


@pytest.mark.usefixtures("seed_analytics_data")
class TestInsightApiIntegration:
    def test_get_insights_with_seeded_data(self, client, auth_headers):
        from common.database import session_factory
        from insights.service import generate_insight

        db = session_factory()()
        try:
            generate_insight(db)
        finally:
            db.close()

        response = client.get("/api/insights", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "summary_text" in data[0]
        assert "recommendations" in data[0]
        assert "key_findings" in data[0]
        assert "is_fallback" in data[0]

    def test_get_insights_requires_auth(self, client):
        response = client.get("/api/insights")

        assert response.status_code == 401

    def test_get_latest_insight_with_seeded_data(self, client, auth_headers):
        from common.database import session_factory
        from insights.service import generate_insight

        db = session_factory()()
        try:
            generate_insight(db)
        finally:
            db.close()

        response = client.get("/api/insights/latest", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "summary_text" in data
        assert "generated_at" in data

    def test_get_latest_insight_404_when_empty(self, client, auth_headers):
        response = client.get("/api/insights/latest", headers=auth_headers)

        assert response.status_code == 404
