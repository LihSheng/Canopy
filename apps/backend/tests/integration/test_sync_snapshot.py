import json
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from common.clock import utcnow
from sync.repositories.snapshot import SnapshotRepository
from sync.schema import SourceSnapshotModel, SourceSnapshotRowModel


@pytest.fixture
def app_session(engine):
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


class TestSnapshotPersistence:
    def test_save_and_retrieve_snapshot(self, app_session):
        repo = SnapshotRepository(app_session)
        model = SourceSnapshotModel(
            id=str(uuid.uuid4()),
            entity_type="departments",
            status="completed",
            started_at=utcnow(),
            completed_at=utcnow(),
            row_count=3,
            snapshot_id=str(uuid.uuid4()),
        )
        saved = repo.save_snapshot(model)
        app_session.commit()

        fetched = app_session.get(SourceSnapshotModel, saved.id)
        assert fetched is not None
        assert fetched.entity_type == "departments"
        assert fetched.status == "completed"
        assert fetched.row_count == 3

    def test_save_snapshot_rows(self, app_session):
        repo = SnapshotRepository(app_session)
        snap_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        model = SourceSnapshotModel(
            id=snap_id,
            entity_type="employees",
            status="completed",
            started_at=utcnow(),
            completed_at=utcnow(),
            row_count=2,
            snapshot_id=run_id,
        )
        repo.save_snapshot(model)

        row = {"source_key": "E001", "full_name": "Alice", "department_key": "D001"}
        rows = repo.save_rows(snap_id, [row])
        app_session.commit()

        assert len(rows) == 1
        assert rows[0].source_key == "E001"
        data = json.loads(rows[0].entity_data)
        assert data["full_name"] == "Alice"
        assert data["department_key"] == "D001"

    def test_multiple_snapshot_rows_reference_same_snapshot(self, app_session):
        repo = SnapshotRepository(app_session)
        snap_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        model = SourceSnapshotModel(
            id=snap_id,
            entity_type="departments",
            status="completed",
            started_at=utcnow(),
            completed_at=utcnow(),
            row_count=3,
            snapshot_id=run_id,
        )
        repo.save_snapshot(model)

        class FakeRow:
            def __init__(self, source_key, name):
                self.source_key = source_key
                self.name = name

        repo.save_rows(
            snap_id,
            [
                FakeRow("D001", "Engineering"),
                FakeRow("D002", "Marketing"),
                FakeRow("D003", "Sales"),
            ],
        )
        app_session.commit()

        rows = (
            app_session.execute(select(SourceSnapshotRowModel).where(SourceSnapshotRowModel.snapshot_id == snap_id))
            .scalars()
            .all()
        )
        assert len(rows) == 3

    def test_snapshot_error_recording(self, app_session):
        repo = SnapshotRepository(app_session)
        error_model = SourceSnapshotModel(
            id=str(uuid.uuid4()),
            entity_type="claims",
            status="failed",
            started_at=utcnow(),
            completed_at=utcnow(),
            row_count=0,
            error_message="no such table: claims",
            snapshot_id=str(uuid.uuid4()),
        )
        saved = repo.save_snapshot(error_model)
        app_session.commit()

        fetched = app_session.get(SourceSnapshotModel, saved.id)
        assert fetched is not None
        assert fetched.status == "failed"
        assert fetched.error_message == "no such table: claims"
        assert fetched.row_count == 0


class TestSnapshotRepositoryExtractors:
    """Cover _extract_source_key and _row_to_dict edge cases (lines 38-54)."""

    def test_extract_source_key_from_object(self):
        """line 40-41: object with source_key attribute."""

        class Obj:
            source_key = "KEY001"

        result = SnapshotRepository._extract_source_key(Obj())
        assert result == "KEY001"

    def test_extract_source_key_from_dict(self):
        """line 42-43: dict with source_key key."""
        result = SnapshotRepository._extract_source_key({"source_key": "KEY002"})
        assert result == "KEY002"

    def test_extract_source_key_unknown(self):
        """line 44: no source_key found -> 'unknown'."""
        result = SnapshotRepository._extract_source_key(42)
        assert result == "unknown"

    def test_row_to_dict_from_dataclass(self):
        """line 48-51: dataclass input."""
        from dataclasses import dataclass

        @dataclass
        class FakeRow:
            source_key: str
            name: str

        result = SnapshotRepository._row_to_dict(FakeRow("K1", "Eng"))
        assert result == {"source_key": "K1", "name": "Eng"}

    def test_row_to_dict_from_dict(self):
        """line 52-53: dict input returns as-is."""
        result = SnapshotRepository._row_to_dict({"a": 1})
        assert result == {"a": 1}

    def test_row_to_dict_fallback(self):
        """line 54: fallback wraps in {'value': str}."""
        result = SnapshotRepository._row_to_dict(42)
        assert result == {"value": "42"}
