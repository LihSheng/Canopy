"""Integration tests for tenant-scoped repository behavior.

Verifies:
- Projects created without tenant_id are filterable
- Projects listed by tenant only return matching tenant rows
- Cross-tenant get returns None when tenant_id filter applied
- list_by_tenant filters correctly
"""

from datetime import UTC, datetime

from project.domain import Project
from project.repository import ProjectRepository
from tests.unit.postgres_test_db import make_postgres_session


def _make_session():
    return make_postgres_session(("project.schema",))


def _a_project(**kwargs) -> Project:
    defaults = {
        "id": "proj-1",
        "tenant_id": "tenant-1",
        "name": "Project 1",
        "description": "desc",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return Project(**defaults)


class TestProjectRepositoryTenantScoping:
    def test_get_with_tenant_filter_returns_correct_project(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1", tenant_id="tenant-1", name="T1 Project"))
            repo.save(_a_project(id="p-t2", tenant_id="tenant-2", name="T2 Project"))

            found = repo.get("p-t1", tenant_id="tenant-1")
            assert found is not None
            assert found.name == "T1 Project"
        finally:
            session.close()

    def test_get_with_cross_tenant_filter_returns_none(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t2", tenant_id="tenant-2", name="T2 Project"))

            found = repo.get("p-t2", tenant_id="tenant-1")
            assert found is None
        finally:
            session.close()

    def test_get_without_tenant_filter_returns_any_project(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1", tenant_id="tenant-1", name="T1 Project"))

            found = repo.get("p-t1")  # no tenant filter
            assert found is not None
            assert found.id == "p-t1"
        finally:
            session.close()

    def test_list_all_filters_by_tenant(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1-a", tenant_id="tenant-1", name="T1-A"))
            repo.save(_a_project(id="p-t1-b", tenant_id="tenant-1", name="T1-B"))
            repo.save(_a_project(id="p-t2-a", tenant_id="tenant-2", name="T2-A"))

            t1_projects = repo.list_all(tenant_id="tenant-1")
            assert len(t1_projects) == 2
            names = {p.name for p in t1_projects}
            assert names == {"T1-A", "T1-B"}

            t2_projects = repo.list_all(tenant_id="tenant-2")
            assert len(t2_projects) == 1
            assert t2_projects[0].name == "T2-A"
        finally:
            session.close()

    def test_list_all_without_tenant_returns_all(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1", tenant_id="tenant-1", name="T1"))
            repo.save(_a_project(id="p-t2", tenant_id="tenant-2", name="T2"))

            all_projects = repo.list_all()
            assert len(all_projects) >= 2
        finally:
            session.close()

    def test_list_by_tenant_is_alias_for_list_all_with_filter(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1", tenant_id="tenant-1"))
            repo.save(_a_project(id="p-t2", tenant_id="tenant-2"))

            t1 = repo.list_by_tenant("tenant-1")
            assert len(t1) == 1
            assert t1[0].id == "p-t1"
        finally:
            session.close()

    def test_delete_with_tenant_filter_only_deletes_owned(self):
        session = _make_session()
        repo = ProjectRepository(session)
        try:
            repo.save(_a_project(id="p-t1", tenant_id="tenant-1"))
            repo.save(_a_project(id="p-t2", tenant_id="tenant-2"))

            # Trying to delete t1's project from t2 should fail
            deleted = repo.delete("p-t1", tenant_id="tenant-2")
            assert deleted is False
            # t1's project should still exist
            assert repo.get("p-t1") is not None
        finally:
            session.close()
