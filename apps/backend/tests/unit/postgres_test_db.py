from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session, sessionmaker

from common.database import Base

_TEST_SERVER_URL = os.environ.get(
    "CANOPY_TEST_SERVER_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432",
)
_TEST_ADMIN_DATABASE_NAME = os.environ.get("CANOPY_TEST_ADMIN_DATABASE_NAME", "postgres")


def _admin_engine() -> Engine:
    url = make_url(_TEST_SERVER_URL).set(database=_TEST_ADMIN_DATABASE_NAME)
    return create_engine(url, isolation_level="AUTOCOMMIT")


def _create_database(database_name: str) -> None:
    admin_engine = _admin_engine()
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            ).scalar()
            if exists:
                return
            conn.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        admin_engine.dispose()


def _reset_database(database_name: str) -> None:
    engine = create_engine(_database_url(database_name))
    try:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS public CASCADE'))
            conn.execute(text('CREATE SCHEMA public'))
    finally:
        engine.dispose()


def _database_name(schema_modules: Iterable[str]) -> str:
    suffix = "_".join(module_name.rsplit(".", 1)[-1] for module_name in schema_modules)
    return f"canopy_unit_{suffix}"


def _database_url(database_name: str):
    return make_url(_TEST_SERVER_URL).set(database=database_name)


@dataclass
class PostgresSessionHandle:
    session: Session
    engine: Engine
    database_name: str

    def __getattr__(self, name: str):
        return getattr(self.session, name)

    def close(self) -> None:
        self.session.close()
        self.engine.dispose()


def make_postgres_session(schema_modules: Iterable[str]) -> PostgresSessionHandle:
    schema_modules = tuple(schema_modules)
    for module_name in schema_modules:
        importlib.import_module(module_name)

    database_name = _database_name(schema_modules)
    _create_database(database_name)

    database_url = _database_url(database_name)
    engine = create_engine(database_url)
    _reset_database(database_name)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    return PostgresSessionHandle(session=session, engine=engine, database_name=database_name)
