"""Integration tests for admin health dashboard endpoints.

Covers all 7 admin health routes plus admin-auth enforcement.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from auth.hashing import hash_password
from auth.schema import UserModel
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from health.schema import PipelineRunTelemetryModel

# ---------------------------------------------------------------------------
# Admin test fixtures
# ---------------------------------------------------------------------------

TEST_TENANT_ID = "tenant-health-test-1"
TEST_PIPELINE_A = "ingestion:dataset-alpha"
TEST_PIPELINE_B = "transform:dataset-beta"


@pytest.fixture
def admin_user(db_session):
    user = UserModel(
        id="admin-health-user",
        email="admin-health@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Health Admin",
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session):
    user = UserModel(
        id="regular-health-user",
        email="regular@canopy.dev",
        password_hash=hash_password("user123"),
        display_name="Regular User",
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_health_tenant(db_session):
    tenant = TenantModel(
        id=TEST_TENANT_ID,
        tenant_uuid=str(uuid.uuid4()),
        name="Health Test Tenant",
        slug="health-test-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture
def seed_admin_membership(db_session, admin_user, seed_health_tenant):
    membership = TenantMembershipModel(
        id="mem-admin-health",
        user_id=admin_user.id,
        tenant_id=TEST_TENANT_ID,
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    return membership


@pytest.fixture
def seed_regular_membership(db_session, regular_user, seed_health_tenant):
    membership = TenantMembershipModel(
        id="mem-regular-health",
        user_id=regular_user.id,
        tenant_id=TEST_TENANT_ID,
        role="member",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    return membership


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Login as admin user to get auth token."""
    response = client.post(
        "/api/auth/login",
        json={"email": "admin-health@canopy.dev", "password": "admin123"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_auth_headers(client, regular_user):
    """Login as regular (non-admin) user to get auth token."""
    response = client.post(
        "/api/auth/login",
        json={"email": "regular@canopy.dev", "password": "user123"},
    )
    assert response.status_code == 200, f"Regular login failed: {response.text}"
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Telemetry seed data
# ---------------------------------------------------------------------------


def _make_telemetry_row(
    pipeline_id: str,
    run_id: str,
    status: str,
    created_at: datetime,
    duration_ms: int = 45000,
    bytes_written: int = 1024 * 1024,
    error_message: str = "",
    warning_message: str = "",
    latency_threshold_ms: int | None = 60000,
) -> PipelineRunTelemetryModel:
    return PipelineRunTelemetryModel(
        id=str(uuid.uuid4()),
        tenant_id=TEST_TENANT_ID,
        pipeline_id=pipeline_id,
        job_type="ingestion" if "ingestion" in pipeline_id else "transform",
        run_id=run_id,
        status=status,
        duration_ms=duration_ms,
        bytes_written=bytes_written,
        rows_processed=100,
        error_message=error_message,
        warning_message=warning_message,
        latency_threshold_ms=latency_threshold_ms,
        started_at=created_at - timedelta(seconds=45),
        finished_at=created_at,
        created_at=created_at,
    )


@pytest.fixture
def seed_telemetry_data(db_session, seed_admin_membership):
    """Seed 5 days of telemetry across 2 pipelines with mixed statuses."""
    today = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)
    models = []

    # Pipeline A -- mostly healthy, 1 failure on day -2, 1 SLA violation on day -1
    for offset in range(5):
        day = today - timedelta(days=offset)
        run_id_success = f"run-a-success-d{offset}"
        run_id_fail = f"run-a-fail-d{offset}"
        run_id_sla = f"run-a-sla-d{offset}"

        models.append(_make_telemetry_row(TEST_PIPELINE_A, run_id_success, "success", day))
        models.append(
            _make_telemetry_row(
                TEST_PIPELINE_A,
                run_id_sla,
                "success",
                day,
                duration_ms=90000,
                bytes_written=5 * 1024 * 1024,
            )
        )

        if offset == 2:
            models.append(
                _make_telemetry_row(
                    TEST_PIPELINE_A,
                    run_id_fail,
                    "failed",
                    day,
                    error_message="Connection timeout to source database",
                )
            )

    # Pipeline B -- failed today, warning yesterday
    run_id_b_fail = "run-b-fail-today"
    run_id_b_warn = "run-b-warn-yesterday"
    run_id_b_ok = "run-b-ok-yesterday"
    models.append(
        _make_telemetry_row(
            TEST_PIPELINE_B,
            run_id_b_fail,
            "failed",
            today,
            error_message="Schema Drift Detected: Column 'cust_id' type changed",
            bytes_written=2 * 1024 * 1024,
        )
    )
    models.append(
        _make_telemetry_row(
            TEST_PIPELINE_B,
            run_id_b_warn,
            "warning",
            today - timedelta(days=1),
            warning_message="High row count detected",
            bytes_written=3 * 1024 * 1024,
        )
    )
    models.append(
        _make_telemetry_row(
            TEST_PIPELINE_B,
            run_id_b_ok,
            "success",
            today - timedelta(days=1),
            bytes_written=1 * 1024 * 1024,
        )
    )

    db_session.add_all(models)
    db_session.commit()
    return models


@pytest.fixture
def seed_rollups(db_session, seed_telemetry_data):
    """Compute rollups for the seeded telemetry data."""
    from health.service import RollupService

    svc = RollupService(db_session)
    today = datetime.now(UTC).date()
    for offset in range(5):
        svc.compute_daily_rollup(TEST_TENANT_ID, today - timedelta(days=offset))
    return True


# ---------------------------------------------------------------------------
# Authorization tests
# ---------------------------------------------------------------------------


class TestAdminHealthAuth:
    """Non-admin users must receive 401 on all admin health routes."""

    ADMIN_ROUTES = [
        ("GET", "/api/admin/health/summary", {}),
        ("GET", "/api/admin/health/trends", {"days": 30}),
        ("GET", "/api/admin/health/pipelines", {}),
        ("GET", f"/api/admin/health/pipelines/{TEST_PIPELINE_A}", {}),
        ("GET", "/api/admin/health/runs/run-a-success-d0", {}),
        ("POST", "/api/admin/health/refresh", {}),
        ("POST", "/api/admin/health/backfill", {"days": 5}),
    ]

    @pytest.mark.parametrize("method,path,params", ADMIN_ROUTES)
    def test_non_admin_blocked(
        self,
        client,
        regular_auth_headers,
        method,
        path,
        params,
    ):
        if method == "GET":
            resp = client.get(path, params=params, headers=regular_auth_headers)
        else:
            resp = client.post(path, params=params, headers=regular_auth_headers)
        assert resp.status_code == 401, (
            f"{method} {path} should return 401 for non-admin, got {resp.status_code}: {resp.text}"
        )


# ---------------------------------------------------------------------------
# Summary endpoint tests
# ---------------------------------------------------------------------------


class TestHealthSummary:
    def test_summary_returns_kpi_fields(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "bytes_written_30d" in data
        assert "error_count_30d" in data
        assert "warning_count_30d" in data
        assert "sla_violation_count_30d" in data
        assert "total_runs_30d" in data
        assert "active_pipeline_count" in data
        assert "recent_failures" in data

    def test_summary_bytes_written_positive(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Each day: Pipeline A has 2 success rows (1MB + 5MB), Pipeline B has varied
        assert data["bytes_written_30d"] > 0

    def test_summary_error_count_detects_failures(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Pipeline A day -2 failure + Pipeline B today failure = 2 failures
        assert data["error_count_30d"] >= 2

    def test_summary_warning_count(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Pipeline B had 1 warning yesterday
        assert data["warning_count_30d"] >= 1

    def test_summary_sla_violation_count(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Pipeline A SLA runs (90000ms > 60000ms threshold) on each day
        assert data["sla_violation_count_30d"] >= 1

    def test_summary_active_pipeline_count(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Two distinct pipelines
        assert data["active_pipeline_count"] == 2

    def test_summary_includes_recent_failures(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        failures = data["recent_failures"]
        assert isinstance(failures, list)
        assert len(failures) >= 1
        # Failures should have error_message field
        assert "error_message" in failures[0]
        assert "pipeline_id" in failures[0]

    def test_summary_no_data_returns_zeros(self, client, admin_auth_headers, seed_admin_membership):
        """Summary without any rollup data should return zero values, not errors."""
        resp = client.get("/api/admin/health/summary", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["bytes_written_30d"] == 0
        assert data["error_count_30d"] == 0
        assert data["active_pipeline_count"] == 0
        assert isinstance(data["recent_failures"], list)


# ---------------------------------------------------------------------------
# Trends endpoint tests
# ---------------------------------------------------------------------------


class TestHealthTrends:
    def test_trends_returns_daily_array(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/trends?days=30", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_trends_contains_expected_fields(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/trends?days=30", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        entry = data[0]
        assert "date" in entry
        assert "bytes_written" in entry
        assert "errors" in entry
        assert "sla_violations" in entry
        assert "run_count" in entry

    def test_trends_default_days(self, client, admin_auth_headers, seed_rollups):
        """Trends without days param should default to 30."""
        resp = client.get("/api/admin/health/trends", headers=admin_auth_headers)
        assert resp.status_code == 200

    def test_trends_custom_window(self, client, admin_auth_headers, seed_rollups):
        """Trends with days=5 should return only dates within 5-day window."""
        resp = client.get("/api/admin/health/trends?days=5", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # Should have at most 5 entries (one per date)
        assert len(data) <= 5

    def test_trends_empty_for_no_data(self, client, admin_auth_headers, seed_admin_membership):
        resp = client.get("/api/admin/health/trends?days=30", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ---------------------------------------------------------------------------
# Pipeline catalog endpoint tests
# ---------------------------------------------------------------------------


class TestPipelineCatalog:
    def test_catalog_lists_all_pipelines(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/pipelines", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_catalog_entry_has_health_state(self, client, admin_auth_headers, seed_rollups):
        resp = client.get("/api/admin/health/pipelines", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        for entry in data:
            assert "pipeline_id" in entry
            assert "health" in entry
            assert entry["health"] in ("healthy", "degraded", "failed")

    def test_catalog_filter_by_health(self, client, admin_auth_headers, seed_rollups):
        """Filtering by health=failed should only return failed pipelines."""
        resp = client.get(
            "/api/admin/health/pipelines?health_filter=failed",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for entry in data:
            assert entry["health"] == "failed"

    def test_catalog_sorted_failed_first(self, client, admin_auth_headers, seed_rollups):
        """Catalog sorts by: failed < degraded < healthy."""
        resp = client.get("/api/admin/health/pipelines", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        if len(data) >= 2:
            # First entries should be failed/degraded before healthy
            health_rank = {"failed": 0, "degraded": 1, "healthy": 2}
            for i in range(len(data) - 1):
                assert health_rank[data[i]["health"]] <= health_rank[data[i + 1]["health"]]

    def test_catalog_empty_for_no_data(self, client, admin_auth_headers, seed_admin_membership):
        resp = client.get("/api/admin/health/pipelines", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0


# ---------------------------------------------------------------------------
# Pipeline detail endpoint tests
# ---------------------------------------------------------------------------


class TestPipelineDetail:
    def test_detail_returns_full_summary(self, client, admin_auth_headers, seed_rollups):
        resp = client.get(
            f"/api/admin/health/pipelines/{TEST_PIPELINE_A}",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pipeline_id" in data
        assert "days_active" in data
        assert "total_runs" in data
        assert "total_failures" in data
        assert "total_successes" in data
        assert "total_warnings" in data
        assert "total_bytes_written" in data
        assert "total_rows_processed" in data
        assert "total_sla_violations" in data
        assert "avg_duration_ms" in data
        assert "max_duration_ms" in data

    def test_detail_includes_recent_runs(self, client, admin_auth_headers, seed_rollups):
        resp = client.get(
            f"/api/admin/health/pipelines/{TEST_PIPELINE_A}",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recent_runs" in data
        assert isinstance(data["recent_runs"], list)
        assert len(data["recent_runs"]) >= 1

    def test_detail_nonexistent_pipeline_returns_404(self, client, admin_auth_headers, seed_admin_membership):
        resp = client.get(
            "/api/admin/health/pipelines/nonexistent-pipeline-999",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Run detail endpoint tests
# ---------------------------------------------------------------------------


class TestRunDetail:
    def test_run_detail_returns_steps(self, client, admin_auth_headers, seed_telemetry_data):
        resp = client.get(
            "/api/admin/health/runs/run-a-fail-d2",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "run_id" in data
        assert data["run_id"] == "run-a-fail-d2"
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) >= 1

    def test_run_detail_step_has_error_message(self, client, admin_auth_headers, seed_telemetry_data):
        resp = client.get(
            "/api/admin/health/runs/run-a-fail-d2",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        step = data["steps"][0]
        assert step["error_message"] == "Connection timeout to source database"
        assert step["status"] == "failed"

    def test_run_detail_nonexistent_returns_404(self, client, admin_auth_headers, seed_admin_membership):
        resp = client.get(
            "/api/admin/health/runs/fake-run-id-0000",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Refresh rollups endpoint tests
# ---------------------------------------------------------------------------


class TestRefreshRollups:
    def test_refresh_computes_today(self, client, admin_auth_headers, seed_telemetry_data):
        resp = client.post("/api/admin/health/refresh", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["refreshed"] is True
        assert "date" in data

    def test_refresh_non_admin_blocked(self, client, regular_auth_headers):
        resp = client.post("/api/admin/health/refresh", headers=regular_auth_headers)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Backfill rollups endpoint tests
# ---------------------------------------------------------------------------


class TestBackfillRollups:
    def test_backfill_computes_rollups(self, client, admin_auth_headers, seed_telemetry_data):
        resp = client.post("/api/admin/health/backfill?days=1", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["backfilled"] is True
        assert data["days"] == 1

    def test_backfill_rejects_invalid_days_zero(self, client, admin_auth_headers):
        resp = client.post("/api/admin/health/backfill?days=0", headers=admin_auth_headers)
        assert resp.status_code == 400

    def test_backfill_rejects_invalid_days_over_max(self, client, admin_auth_headers):
        resp = client.post("/api/admin/health/backfill?days=200", headers=admin_auth_headers)
        assert resp.status_code == 400

    def test_backfill_non_admin_blocked(self, client, regular_auth_headers):
        resp = client.post("/api/admin/health/backfill?days=1", headers=regular_auth_headers)
        assert resp.status_code == 401
