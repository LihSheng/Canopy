from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.config import settings


class _SourceDatabaseManager:
    """Encapsulates engine and session factory lifecycle for the read-only source database."""

    def __init__(self):
        self._source_engine: Engine | None = None
        self._source_session_factory: sessionmaker[Session] | None = None

    def _build_source_engine(self) -> Engine:
        connect_args: dict[str, bool] = {"check_same_thread": False}
        engine_kwargs: dict[str, object] = {}
        url = settings.source_database_url
        if ":memory:" in url:
            engine_kwargs["poolclass"] = StaticPool
        return create_engine(url, connect_args=connect_args, **engine_kwargs)

    def source_engine(self) -> Engine:
        if self._source_engine is None:
            self._source_engine = self._build_source_engine()
        return self._source_engine

    def source_session_factory(self) -> sessionmaker[Session]:
        if self._source_session_factory is None:
            self._source_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self.source_engine())
        return self._source_session_factory

    def set_source_engine(self, eng: Engine) -> None:
        self._source_engine = eng
        self._source_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)

    def reset_source_engine(self) -> None:
        self._source_engine = None
        self._source_session_factory = None


# Module-level default instance.
_source_db_manager = _SourceDatabaseManager()


# Public API delegates to the default instance.


def source_engine() -> Engine:
    return _source_db_manager.source_engine()


def source_session_factory() -> sessionmaker[Session]:
    return _source_db_manager.source_session_factory()


def set_source_engine(eng: Engine) -> None:
    _source_db_manager.set_source_engine(eng)


def reset_source_engine() -> None:
    _source_db_manager.reset_source_engine()
