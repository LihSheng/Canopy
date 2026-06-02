import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError
from project.domain import Project
from project.repository import ProjectRepository


class ProjectService:
    def __init__(self, repo: ProjectRepository):
        self._repo = repo

    def create_project(self, tenant_id: str, name: str, description: str = "") -> Project:
        now = datetime.now(UTC)
        project = Project(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            created_at=now,
        )
        return self._repo.save(project)

    def get_project(self, id: str, tenant_id: str | None = None) -> Project | None:
        return self._repo.get(id, tenant_id=tenant_id)

    def list_projects(self, tenant_id: str | None = None) -> list[Project]:
        return self._repo.list_all(tenant_id=tenant_id)

    def require_project(self, id: str, tenant_id: str | None = None) -> Project:
        project = self._repo.get(id, tenant_id=tenant_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project
