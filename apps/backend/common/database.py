from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from common.config import settings


class _DatabaseManager:
    """Encapsulates engine and session factory lifecycle for control-plane and tenant-data databases.

    A single module-level instance is used by default. Future multi-tenant routing
    can introduce per-request instances without changing business service signatures.
    """

    def __init__(self):
        self._control_plane_engine: Engine | None = None
        self._tenant_data_engine: Engine | None = None
        self._control_plane_session_factory: sessionmaker[Session] | None = None
        self._tenant_data_session_factory: sessionmaker[Session] | None = None

    def _build_engine(self, database_url: str) -> Engine:
        return create_engine(database_url)

    def _resolve_control_plane_engine(self) -> Engine:
        if self._control_plane_engine is None:
            self._control_plane_engine = self._build_engine(settings.resolved_control_plane_database_url)
        return self._control_plane_engine

    def _resolve_tenant_data_engine(self) -> Engine:
        if self._tenant_data_engine is None:
            self._tenant_data_engine = self._build_engine(settings.resolved_tenant_data_database_url)
        return self._tenant_data_engine

    def _resolve_session_factory(self, *, tenant_data: bool = False) -> sessionmaker[Session]:
        if tenant_data:
            if self._tenant_data_session_factory is None:
                self._tenant_data_session_factory = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._resolve_tenant_data_engine(),
                )
            return self._tenant_data_session_factory

        if self._control_plane_session_factory is None:
            self._control_plane_session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._resolve_control_plane_engine(),
            )
        return self._control_plane_session_factory

    def engine(self) -> Engine:
        return self._resolve_control_plane_engine()

    def control_plane_engine(self) -> Engine:
        return self._resolve_control_plane_engine()

    def tenant_data_engine(self) -> Engine:
        return self._resolve_tenant_data_engine()

    def session_factory(self) -> sessionmaker[Session]:
        return self._resolve_session_factory()

    def control_plane_session_factory(self) -> sessionmaker[Session]:
        return self._resolve_session_factory()

    def tenant_data_session_factory(self) -> sessionmaker[Session]:
        return self._resolve_session_factory(tenant_data=True)

    def set_engine(self, eng: Engine, tenant_data_eng: Engine | None = None) -> None:
        self._control_plane_engine = eng
        self._tenant_data_engine = tenant_data_eng or eng
        self._control_plane_session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._control_plane_engine
        )
        self._tenant_data_session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._tenant_data_engine
        )

    def reset_engine(self) -> None:
        self._control_plane_engine = None
        self._tenant_data_engine = None
        self._control_plane_session_factory = None
        self._tenant_data_session_factory = None


# Module-level default instance. Replaceable for testing or per-tenant routing.
_db_manager = _DatabaseManager()


# Public API delegates to the default instance so callers do not touch globals directly.


def engine() -> Engine:
    return _db_manager.engine()


def control_plane_engine() -> Engine:
    return _db_manager.control_plane_engine()


def tenant_data_engine() -> Engine:
    return _db_manager.tenant_data_engine()


def session_factory() -> sessionmaker[Session]:
    return _db_manager.session_factory()


def control_plane_session_factory() -> sessionmaker[Session]:
    return _db_manager.control_plane_session_factory()


def tenant_data_session_factory() -> sessionmaker[Session]:
    return _db_manager.tenant_data_session_factory()


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
    _db_manager.set_engine(eng, tenant_data_eng)


def reset_engine() -> None:
    _db_manager.reset_engine()


class Base(DeclarativeBase):
    pass


def get_db():
    db = control_plane_session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_override: Engine | None = None):
    import analytics.schema  # noqa: F401  ensure analytics models are registered
    import anomalies.schema  # noqa: F401  ensure anomaly models are registered
    import auth.schema  # noqa: F401  ensure UserModel is registered
    import connection.schema  # noqa: F401  ensure connection models are registered
    import control_plane.schemas.audit  # noqa: F401
    import control_plane.schemas.config  # noqa: F401
    import control_plane.schemas.database_targets  # noqa: F401
    import control_plane.schemas.jobs  # noqa: F401
    import control_plane.schemas.memberships  # noqa: F401
    import control_plane.schemas.tenants  # noqa: F401
    import dataset.schema  # noqa: F401  ensure dataset models are registered
    import exports.schema  # noqa: F401  ensure export models are registered
    import ingestion.schema  # noqa: F401  ensure ingestion models are registered
    import insights.schema  # noqa: F401  ensure insight models are registered
    import ontology.schema  # noqa: F401  ensure ontology models are registered
    import project.schema  # noqa: F401  ensure project models are registered
    import refresh.schema  # noqa: F401  ensure refresh models are registered
    import run.schema  # noqa: F401  ensure run models are registered
    import source_type.schema  # noqa: F401  ensure source type models are registered
    import sync.schema  # noqa: F401  ensure SourceSnapshotModel is registered
    import tenant_data.schemas.clean  # noqa: F401
    import tenant_data.schemas.metadata  # noqa: F401
    import tenant_data.schemas.raw  # noqa: F401
    import tenant_data.schemas.staging  # noqa: F401
    from tenant_data.base import TenantDataBase

    control_plane_eng = engine_override or control_plane_engine()
    tenant_data_eng = engine_override or tenant_data_engine()
    Base.metadata.create_all(bind=control_plane_eng)
    TenantDataBase.metadata.create_all(bind=tenant_data_eng)
