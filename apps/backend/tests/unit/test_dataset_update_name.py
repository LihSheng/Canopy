from __future__ import annotations

from common.errors import NotFoundError, ValidationError
from connection.domain import Connection
from connection.repository import ConnectionRepository
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService
from tests.unit.postgres_test_db import make_postgres_session


def _make_session():
    return make_postgres_session(("connection.schema", "dataset.schema"))


def _create_test_dataset(session) -> str:
    conn_repo = ConnectionRepository(session)
    conn_repo.save(
        Connection(
            id="conn-1",
            project_id="proj-1",
            source_type="mysql",
            name="MySQL",
            config_json={"host": "127.0.0.1", "database": "tenant_demo", "username": "homestead"},
        )
    )
    service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))
    dataset = service.create_dataset(
        project_id="proj-1",
        connection_id="conn-1",
        name="employees",
        source_object_name="employees",
        defer_materialization=True,
    )
    return dataset.id


def test_renames_dataset_successfully():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        updated = service.update_dataset_name(dataset_id, "Employees 2024")

        assert updated.name == "Employees 2024"
        assert updated.id == dataset_id

        fetched = service.get_dataset(dataset_id)
        assert fetched is not None
        assert fetched.name == "Employees 2024"
    finally:
        session.close()


def test_rename_raises_not_found_for_missing_dataset():
    session = _make_session()
    try:
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))
        try:
            service.update_dataset_name("nonexistent", "New Name")
            assert False, "Expected NotFoundError"
        except NotFoundError:
            pass
    finally:
        session.close()


def test_rename_rejects_empty_name():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        try:
            service.update_dataset_name(dataset_id, "")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "must not be empty" in str(e).lower()
    finally:
        session.close()


def test_rename_rejects_whitespace_only_name():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        try:
            service.update_dataset_name(dataset_id, "   ")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "must not be empty" in str(e).lower()
    finally:
        session.close()


def test_rename_rejects_name_starting_with_digit():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        try:
            service.update_dataset_name(dataset_id, "2nd Quarter")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "start with a letter" in str(e).lower()
    finally:
        session.close()


def test_rename_rejects_name_with_special_characters():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        try:
            service.update_dataset_name(dataset_id, "Payroll@2024!")
            assert False, "Expected ValidationError"
        except ValidationError as e:
            assert "invalid characters" in str(e).lower()
    finally:
        session.close()


def test_rename_allows_hyphens_and_underscores():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        updated = service.update_dataset_name(dataset_id, "Payroll-Data_2024")
        assert updated.name == "Payroll-Data_2024"
    finally:
        session.close()


def test_rename_trims_whitespace():
    session = _make_session()
    try:
        dataset_id = _create_test_dataset(session)
        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))

        updated = service.update_dataset_name(dataset_id, "  Payroll  ")
        assert updated.name == "Payroll"
    finally:
        session.close()
