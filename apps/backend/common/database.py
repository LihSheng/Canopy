
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.config import settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _build_engine(database_url: str) -> Engine:
    connect_args: dict = {}
    engine_kwargs: dict = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool
    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


def _resolve_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = _build_engine(settings.database_url)
    return _engine


def _resolve_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=_resolve_engine())
    return _session_factory


def engine() -> Engine:
    return _resolve_engine()


def session_factory() -> sessionmaker[Session]:
    return _resolve_session_factory()


def set_engine(eng: Engine) -> None:
    global _engine, _session_factory
    _engine = eng
    _session_factory = sessionmaker(autocommit=False, autoflush=False, bind=eng)


def reset_engine() -> None:
    global _engine, _session_factory
    _engine = None
    _session_factory = None


class Base(DeclarativeBase):
    pass


def get_db():
    db = session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_override: Engine | None = None):
    import auth.schema  # noqa: F401  ensure UserModel is registered
    import sync.schema  # noqa: F401  ensure SourceSnapshotModel is registered
    import ontology.schema  # noqa: F401  ensure ontology models are registered

    eng = engine_override or engine()
    Base.metadata.create_all(bind=eng)
