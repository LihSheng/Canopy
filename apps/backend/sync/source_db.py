from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.config import settings

_source_engine: Engine | None = None
_source_session_factory: sessionmaker[Session] | None = None


def _build_source_engine() -> Engine:
    connect_args: dict[str, bool] = {"check_same_thread": False}
    engine_kwargs: dict[str, object] = {}
    url = settings.source_database_url
    if ":memory:" in url:
        engine_kwargs["poolclass"] = StaticPool
    return create_engine(url, connect_args=connect_args, **engine_kwargs)


def source_engine() -> Engine:
    global _source_engine
    if _source_engine is None:
        _source_engine = _build_source_engine()
    return _source_engine


def source_session_factory() -> sessionmaker[Session]:
    global _source_session_factory
    if _source_session_factory is None:
        _source_session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=source_engine()
        )
    return _source_session_factory


def set_source_engine(eng: Engine) -> None:
    global _source_engine, _source_session_factory
    _source_engine = eng
    _source_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)


def reset_source_engine() -> None:
    global _source_engine, _source_session_factory
    _source_engine = None
    _source_session_factory = None
