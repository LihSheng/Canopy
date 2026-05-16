import pytest

pytestmark = pytest.mark.integration


class _InlineThread:
    def __init__(self, target, args=(), kwargs=None, **_):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        self._target(*self._args, **self._kwargs)


@pytest.mark.usefixtures("seed_analytics_data")
class TestExportJobsV2:
    def test_trigger_history_status_and_download(self, client, auth_headers, monkeypatch):
        from exports import service as export_service

        monkeypatch.setattr(export_service.threading, "Thread", _InlineThread)

        trigger_response = client.post(
            "/api/exports/trigger",
            json={"preset_name": "department_spend", "time_range": "last_3_months"},
            headers=auth_headers,
        )
        assert trigger_response.status_code == 200
        payload = trigger_response.json()
        assert payload["accepted"] is True
        job_id = payload["job_id"]

        history_response = client.get("/api/exports/history", headers=auth_headers)
        assert history_response.status_code == 200
        history = history_response.json()["jobs"]
        assert len(history) == 1
        assert history[0]["id"] == job_id
        assert history[0]["preset_name"] == "Department Spend"
        assert history[0]["status"] == "completed"
        assert history[0]["snapshot_id"] == "test-snapshot-001"
        assert history[0]["time_range"] == "last_3_months"

        job_response = client.get(f"/api/exports/jobs/{job_id}", headers=auth_headers)
        assert job_response.status_code == 200
        job = job_response.json()
        assert job["id"] == job_id
        assert job["status"] == "completed"
        assert job["preset_name"] == "Department Spend"
        assert job["snapshot_id"] == "test-snapshot-001"

        download_response = client.get(
            f"/api/exports/jobs/{job_id}/download",
            headers=auth_headers,
        )
        assert download_response.status_code == 200
        assert "department-spend" in download_response.headers["content-disposition"]
        assert download_response.content[:2] == b"PK"

    def test_rerun_keeps_same_snapshot_basis(self, client, auth_headers, monkeypatch):
        from exports import service as export_service

        monkeypatch.setattr(export_service.threading, "Thread", _InlineThread)

        first = client.post(
            "/api/exports/trigger",
            json={"preset_name": "anomaly_review"},
            headers=auth_headers,
        )
        first_job_id = first.json()["job_id"]

        rerun = client.post(
            f"/api/exports/jobs/{first_job_id}/rerun",
            headers=auth_headers,
        )
        assert rerun.status_code == 200
        rerun_job_id = rerun.json()["job_id"]

        first_job = client.get(f"/api/exports/jobs/{first_job_id}", headers=auth_headers).json()
        rerun_job = client.get(f"/api/exports/jobs/{rerun_job_id}", headers=auth_headers).json()

        assert first_job["snapshot_id"] == "test-snapshot-001"
        assert rerun_job["snapshot_id"] == first_job["snapshot_id"]
        assert rerun_job["preset_name"] == first_job["preset_name"] == "Anomaly Review"
