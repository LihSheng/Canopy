
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from common.config import settings

_control_plane_engine: Engine | None = None
_tenant_data_engine: Engine | None = None
_control_plane_session_factory: sessionmaker[Session] | None = None
_tenant_data_session_factory: sessionmaker[Session] | None = None


def _build_engine(database_url: str) -> Engine:
    return create_engine(database_url)


def _resolve_control_plane_engine() -> Engine:
    global _control_plane_engine
    if _control_plane_engine is None:
        _control_plane_engine = _build_engine(settings.resolved_control_plane_database_url)
    return _control_plane_engine


def _resolve_tenant_data_engine() -> Engine:
    global _tenant_data_engine
    if _tenant_data_engine is None:
        _tenant_data_engine = _build_engine(settings.resolved_tenant_data_database_url)
    return _tenant_data_engine


def _resolve_session_factory(
    *, tenant_data: bool = False
) -> sessionmaker[Session]:
    global _control_plane_session_factory, _tenant_data_session_factory
    if tenant_data:
        if _tenant_data_session_factory is None:
            _tenant_data_session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=_resolve_tenant_data_engine(),
            )
        return _tenant_data_session_factory

    if _control_plane_session_factory is None:
        _control_plane_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_resolve_control_plane_engine(),
        )
    return _control_plane_session_factory


def engine() -> Engine:
    return _resolve_control_plane_engine()


def control_plane_engine() -> Engine:
    return _resolve_control_plane_engine()


def tenant_data_engine() -> Engine:
    return _resolve_tenant_data_engine()


def session_factory() -> sessionmaker[Session]:
    return _resolve_session_factory()


def control_plane_session_factory() -> sessionmaker[Session]:
    return _resolve_session_factory()


def tenant_data_session_factory() -> sessionmaker[Session]:
    return _resolve_session_factory(tenant_data=True)


def make_session(session_source):
    if hasattr(session_source, "class_") and hasattr(session_source, "kw"):
        candidate = session_source()
        if not isinstance(candidate, Session):
            raise TypeError("Expected a SQLAlchemy Session from sessionmaker")
        return candidate

    candidate = session_source() if callable(session_source) else session_source
    if not isinstance(candidate, Session):
        raise TypeError("Expected a SQLAlchemy Session or session factory")
    if candidate.bind is None:
        raise RuntimeError("Session does not have an engine bind")
    return sessionmaker(autocommit=False, autoflush=False, bind=candidate.bind)()


def set_engine(eng: Engine, tenant_data_eng: Engine | None = None) -> None:
    global _control_plane_engine, _tenant_data_engine
    global _control_plane_session_factory, _tenant_data_session_factory
    _control_plane_engine = eng
    _tenant_data_engine = tenant_data_eng or eng
    _control_plane_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=_control_plane_engine
    )
    _tenant_data_session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=_tenant_data_engine
    )


def reset_engine() -> None:
    global _control_plane_engine, _tenant_data_engine
    global _control_plane_session_factory, _tenant_data_session_factory
    _control_plane_engine = None
    _tenant_data_engine = None
    _control_plane_session_factory = None
    _tenant_data_session_factory = None


class Base(DeclarativeBase):
    pass


def get_db():
    db = control_plane_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_override: Engine | None = None):
    import ingestion.schema  # noqa: F401  ensure ingestion models are registered
    import auth.schema  # noqa: F401  ensure UserModel is registered
    import sync.schema  # noqa: F401  ensure SourceSnapshotModel is registered
    import ontology.schema  # noqa: F401  ensure ontology models are registered
    import analytics.schema  # noqa: F401  ensure analytics models are registered
    import anomalies.schema  # noqa: F401  ensure anomaly models are registered
    import insights.schema  # noqa: F401  ensure insight models are registered
    import refresh.schema  # noqa: F401  ensure refresh models are registered
    import exports.schema  # noqa: F401  ensure export models are registered
    import project.schema  # noqa: F401  ensure project models are registered
    import source_type.schema  # noqa: F401  ensure source type models are registered
    import connection.schema  # noqa: F401  ensure connection models are registered
    import dataset.schema  # noqa: F401  ensure dataset models are registered
    import run.schema  # noqa: F401  ensure run models are registered
    import control_plane.schemas.audit  # noqa: F401
    import control_plane.schemas.config  # noqa: F401
    import control_plane.schemas.database_targets  # noqa: F401
    import control_plane.schemas.jobs  # noqa: F401
    import control_plane.schemas.memberships  # noqa: F401
    import control_plane.schemas.tenants  # noqa: F401
    import tenant_data.schemas.clean  # noqa: F401
    import tenant_data.schemas.metadata  # noqa: F401
    import tenant_data.schemas.raw  # noqa: F401
    import tenant_data.schemas.staging  # noqa: F401
    from tenant_data.base import TenantDataBase

    control_plane_eng = engine_override or control_plane_engine()
    tenant_data_eng = engine_override or tenant_data_engine()
    Base.metadata.create_all(bind=control_plane_eng)
    TenantDataBase.metadata.create_all(bind=tenant_data_eng)

