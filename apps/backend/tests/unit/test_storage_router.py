import pytest
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from common.database import Base
from control_plane.schemas.database_targets import TenantDatabaseTargetModel
from tenant_data.storage_router import StorageRouter


def _create_control_plane_session_factory(engine):
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _seed_target(session, tenant_id, database_kind="tenant_data", connection_ref="postgresql://..."):
    target = TenantDatabaseTargetModel(
        id=f"target-{tenant_id}",
        tenant_id=tenant_id,
        database_kind=database_kind,
        connection_ref=connection_ref,
        status="active",
    )
    session.add(target)
    session.commit()
    return target


class TestStorageRouterResolveTarget:
    def test_resolve_target_returns_correct_kind_and_ref(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        session = factory()
        _seed_target(session, "tenant-a", database_kind="tenant_data", connection_ref="postgresql://...")
        session.close()

        result = router.resolve_target("tenant-a")
        assert result["database_kind"] == "tenant_data"
        assert result["connection_ref"] == "postgresql://..."
        assert result["tenant_id"] == "tenant-a"

    def test_resolve_target_raises_when_no_target_found(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        with pytest.raises(ValueError, match="No active database target"):
            router.resolve_target("tenant-nonexistent")

    def test_resolve_target_caches_results(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        session = factory()
        _seed_target(session, "tenant-cached", database_kind="tenant_data", connection_ref="postgresql://cached")
        session.close()

        result1 = router.resolve_target("tenant-cached")
        result2 = router.resolve_target("tenant-cached")

        assert result1 is result2
        assert len(router._target_cache) == 1

    def test_resolve_target_skips_inactive_targets(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        session = factory()
        target = TenantDatabaseTargetModel(
            id="target-inactive",
            tenant_id="tenant-inactive",
            database_kind="tenant_data",
            connection_ref="postgresql://inactive",
            status="inactive",
        )
        session.add(target)
        session.commit()
        session.close()

        with pytest.raises(ValueError, match="No active database target"):
            router.resolve_target("tenant-inactive")


class TestStorageRouterCacheInvalidation:
    def test_invalidate_cache_by_tenant_id(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        session = factory()
        _seed_target(session, "tenant-a")
        _seed_target(session, "tenant-b")
        session.close()

        router.resolve_target("tenant-a")
        router.resolve_target("tenant-b")
        assert len(router._target_cache) == 2

        router.invalidate_cache("tenant-a")
        assert "tenant-a" not in router._target_cache
        assert "tenant-b" in router._target_cache
        assert len(router._target_cache) == 1

    def test_invalidate_cache_all(self, engine):
        factory = _create_control_plane_session_factory(engine)
        router = StorageRouter(control_plane_session_factory=factory)

        session = factory()
        _seed_target(session, "tenant-a")
        _seed_target(session, "tenant-b")
        session.close()

        router.resolve_target("tenant-a")
        router.resolve_target("tenant-b")
        assert len(router._target_cache) == 2

        router.invalidate_cache()
        assert len(router._target_cache) == 0


class TestStorageRouterRouteTransaction:
    def test_route_transaction_commits(self, engine):
        factory = _create_control_plane_session_factory(engine)
        session = factory()
        _seed_target(session, "tenant-tx", connection_ref="postgresql://localhost/test")
        session.close()

        router = StorageRouter(
            control_plane_session_factory=factory,
            tenant_data_engine=engine,
        )

        with router.route_transaction("tenant-tx") as td_session:
            dialect_name = td_session.bind.dialect.name if td_session.bind else ""
            if dialect_name == "postgresql":
                td_session.execute(text("SELECT current_setting('app.current_tenant_id', true)"))

    def test_route_transaction_rolls_back_on_error(self, engine):
        factory = _create_control_plane_session_factory(engine)
        session = factory()
        _seed_target(session, "tenant-err", connection_ref="postgresql://localhost/test")
        session.close()

        router = StorageRouter(
            control_plane_session_factory=factory,
            tenant_data_engine=engine,
        )

        with pytest.raises(ValueError):
            with router.route_transaction("tenant-err"):
                raise ValueError("simulated error")

    def test_get_tenant_session_raises_when_no_engine(self, engine):
        factory = _create_control_plane_session_factory(engine)
        session = factory()
        _seed_target(session, "tenant-no-engine", connection_ref="postgresql://...")
        session.close()

        router = StorageRouter(control_plane_session_factory=factory)

        with pytest.raises(RuntimeError, match="Tenant data engine not configured"):
            router.get_tenant_session("tenant-no-engine")

    def test_set_tenant_context_sets_session_variable(self, engine):
        td_session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        td_session = td_session_factory()

        router = StorageRouter(control_plane_session_factory=lambda: None)
        router.set_tenant_context(td_session, "tenant-x")
        dialect_name = td_session.bind.dialect.name if td_session.bind else ""
        if dialect_name == "postgresql":
            value = td_session.execute(text("SELECT current_setting('app.current_tenant_id')")).scalar()
            assert value == "tenant-x"

        td_session.close()
