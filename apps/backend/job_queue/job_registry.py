import threading
import time
import uuid
from enum import Enum


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobRegistry:
    def __init__(self):
        self._lock = threading.Lock()
        self._jobs: dict[str, dict] = {}

    def register_job(self, tenant_id: str, job_type: str) -> str:
        job_id = str(uuid.uuid4())
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "tenant_id": tenant_id,
                "job_type": job_type,
                "status": JobStatus.PENDING.value,
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }
        return job_id

    def update_status(self, job_id: str, status: str, error: str | None = None) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job["status"] = status
            if status == JobStatus.RUNNING.value and job["started_at"] is None:
                job["started_at"] = time.time()
            if status in (JobStatus.COMPLETED.value, JobStatus.FAILED.value):
                job["finished_at"] = time.time()
            if error is not None:
                job["error_message"] = error

    def get_job(self, job_id: str) -> dict | None:
        with self._lock:
            return self._jobs.get(job_id)

    def get_tenant_active_jobs(self, tenant_id: str) -> int:
        with self._lock:
            count = 0
            for job in self._jobs.values():
                if job["tenant_id"] == tenant_id and job["status"] == JobStatus.RUNNING.value:
                    count += 1
            return count

    def get_tenant_jobs(self, tenant_id: str, status: str | None = None) -> list[dict]:
        with self._lock:
            result = []
            for job in self._jobs.values():
                if job["tenant_id"] != tenant_id:
                    continue
                if status is not None and job["status"] != status:
                    continue
                result.append(dict(job))
            return result
