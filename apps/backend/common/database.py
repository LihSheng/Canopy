from collections.abc import Callable

from sqlalchemy import JSON, Column, DefaultClause, Engine, create_engine, inspect, literal, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import CreateColumn

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


def tenant_data_engine() -> Engine:
    return _db_manager.tenant_data_engine()


def session_factory() -> sessionmaker[Session]:
    return _db_manager.session_factory()


def tenant_data_session_factory() -> sessionmaker[Session]:
    return _db_manager.tenant_data_session_factory()


def fresh_session(factory: Callable[[], Session]) -> Session:
    candidate = factory()
    return sessionmaker(autocommit=False, autoflush=False, bind=candidate.bind)()


def set_engine(eng: Engine, tenant_data_eng: Engine | None = None) -> None:
    _db_manager.set_engine(eng, tenant_data_eng)


def reset_engine() -> None:
    _db_manager.reset_engine()


class Base(DeclarativeBase):
    pass


def get_db():
    db = session_factory()()
    try:
        yield db
    finally:
        db.close()


def init_db(engine_override: Engine | None = None):
    import common._all_models  # noqa: F401  register all control-plane models with Base.metadata
    import tenant_data._all_models  # noqa: F401  register all tenant-data models with TenantDataBase.metadata
    from tenant_data.base import TenantDataBase

    control_plane_eng = engine_override or engine()
    tenant_data_eng = engine_override or tenant_data_engine()
    Base.metadata.create_all(bind=control_plane_eng)
    _sync_missing_columns(control_plane_eng, Base.metadata)
    TenantDataBase.metadata.create_all(bind=tenant_data_eng)
    _sync_missing_columns(tenant_data_eng, TenantDataBase.metadata)


def _sync_missing_columns(engine: Engine, metadata) -> None:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    if not existing_tables:
        return

    with engine.begin() as conn:
        for table in metadata.sorted_tables:
            if table.name not in existing_tables:
                continue

            existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
            missing_columns = [column for column in table.columns if column.name not in existing_columns]
            for column in missing_columns:
                add_column = Column(
                    column.name,
                    column.type,
                    nullable=column.nullable,
                    primary_key=column.primary_key,
                    autoincrement=column.autoincrement,
                    unique=column.unique,
                    index=column.index,
                    comment=column.comment,
                    server_default=column.server_default,
                )
                if not add_column.nullable and add_column.server_default is None:
                    default_value = None
                    if column.default is not None and getattr(column.default, "is_scalar", False):
                        default_value = column.default.arg

                    if default_value is not None:
                        default_sql = str(
                            literal(default_value).compile(
                                dialect=engine.dialect,
                                compile_kwargs={"literal_binds": True},
                            )
                        )
                        add_column.server_default = DefaultClause(text(default_sql))
                    elif engine.dialect.name == "postgresql" and isinstance(column.type, JSON):
                        # SQLAlchemy JSON columns often use callable defaults (e.g. default=list),
                        # which are not representable as scalar defaults in DDL compilation here.
                        # For schema sync, prefer a safe empty JSON value to satisfy NOT NULL.
                        add_column.server_default = DefaultClause(text("'[]'::json"))

                column_sql = str(CreateColumn(add_column).compile(dialect=engine.dialect))
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN {column_sql}'))
