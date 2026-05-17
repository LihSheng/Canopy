import uuid
from datetime import UTC, datetime

from v4.run.domain import Run, RunStatus
from v4.run.repository import RunRepository


class RunService:
    def __init__(self, repo: RunRepository):
        self._repo = repo

    def create_run(self, project_id: str, connection_id: str, dataset_id: str, started_by: str = "") -> Run:
        now = datetime.now(UTC)
        run = Run(
            id=str(uuid.uuid4()),
            project_id=project_id,
            connection_id=connection_id,
            dataset_id=dataset_id,
            status=RunStatus.QUEUED.value,
            started_by=started_by,
            created_at=now,
        )
        return self._repo.save(run)

    def get_run(self, id: str) -> Run | None:
        return self._repo.get(id)

    def list_all_runs(self) -> list[Run]:
        return self._repo.list_all()

    def list_runs_by_dataset(self, dataset_id: str) -> list[Run]:
        return self._repo.list_by_dataset(dataset_id)

    def list_runs_by_project(self, project_id: str) -> list[Run]:
        return self._repo.list_by_project(project_id)
