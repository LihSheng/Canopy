import uuid
from datetime import UTC, datetime

from v4.project.domain import Project
from v4.project.repository import ProjectRepository


class ProjectService:
    def __init__(self, repo: ProjectRepository):
        self._repo = repo

    def create_project(self, name: str, description: str = "") -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=now,
        )
        return self._repo.save(project)

    def get_project(self, id: str) -> Project | None:
        return self._repo.get(id)

    def list_projects(self) -> list[Project]:
        return self._repo.list_all()
