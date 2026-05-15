from anomalies.service import detect_anomalies


class TestAnomalyPersistence:
    def test_detect_anomalies_persists_data(self, db_session, seed_analytics_data):
        results = detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        assert len(results) > 0
        for r in results:
            assert r.id
            assert r.snapshot_id == "test-snapshot-001"
            assert r.anomaly_type in (
                "department_total_spike",
                "department_claim_spike",
            )
            assert r.target_entity_id
            assert r.month_key == "2026-05"
            assert r.severity in ("low", "medium", "high")

    def test_get_anomalies_list_returns_mapped_items(self, db_session, seed_analytics_data):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        from anomalies.service import get_anomalies_list
        items = get_anomalies_list(db_session)

        assert len(items) > 0
        for item in items:
            assert "id" in item
            assert "department_id" in item
            assert "department_name" in item
            assert "period" in item
            assert "severity" in item
            assert "change_pct" in item
            assert "description" in item

    def test_get_anomaly_detail_returns_full_data(self, db_session, seed_analytics_data):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        from anomalies.service import get_anomalies_list, get_anomaly_detail
        items = get_anomalies_list(db_session)
        assert len(items) > 0

        detail = get_anomaly_detail(db_session, items[0]["id"])
        assert detail is not None
        assert "baseline_value" in detail
        assert "observed_value" in detail
        assert "delta_value" in detail
        assert "delta_percent" in detail
        assert "driver_details" in detail
        assert isinstance(detail["driver_details"], list)

    def test_clear_snapshot_removes_anomalies(self, db_session, seed_analytics_data):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        from anomalies.repository import AnomalyRepository
        repo = AnomalyRepository(db_session)
        assert repo.count_for_snapshot("test-snapshot-001") > 0

        repo.clear_snapshot("test-snapshot-001")
        assert repo.count_for_snapshot("test-snapshot-001") == 0
