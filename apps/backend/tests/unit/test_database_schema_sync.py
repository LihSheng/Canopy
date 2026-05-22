from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table, create_engine, inspect
from sqlalchemy.orm import sessionmaker

from common.database import Base, init_db, reset_engine, set_engine
from connection.repository import ConnectionRepository
from connection.service import ConnectionService


def test_init_db_backfills_missing_connection_columns(tmp_path):
    engine = create_engine(
        f"sqlite:///{(tmp_path / 'schema-sync.db').as_posix()}",
        connect_args={"check_same_thread": False},
    )

    legacy_metadata = MetaData()
    Table(
        "connections",
        legacy_metadata,
        Column("id", String(36), primary_key=True),
        Column("project_id", String(36), nullable=False),
        Column("source_type", String(255), nullable=False),
        Column("name", String(255), nullable=False),
        Column("status", String(50), nullable=False),
        Column("config_json", JSON, nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False),
        Column("updated_at", DateTime(timezone=True), nullable=False),
    )
    legacy_metadata.create_all(bind=engine)

    set_engine(engine, engine)
    try:
        init_db(engine_override=engine)

        inspector = inspect(engine)
        column_names = {column["name"] for column in inspector.get_columns("connections")}
        assert "test_status" in column_names
        assert "last_tested_at" in column_names

        session = sessionmaker(bind=engine)()
        try:
            service = ConnectionService(ConnectionRepository(session))
            saved = service.create_connection(
                project_id="project-1",
                source_type="static_file",
                name="legacy.xlsx",
                config_json={"file_name": "legacy.xlsx"},
            )

            assert saved.id
            assert saved.test_status is None
        finally:
            session.close()
    finally:
        Base.metadata.drop_all(bind=engine)
        reset_engine()
