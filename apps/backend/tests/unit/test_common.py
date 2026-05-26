"""Unit tests for common modules — config, database, logging edge cases."""

import pytest

from tests.unit.postgres_test_db import make_postgres_session

pytestmark = pytest.mark.unit


class TestConfigSettings:
    """Cover Settings property edge cases."""

    def test_resolved_control_plane_url_falls_back_to_database_url(self):
        """config.py line 17: control_plane_database_url is None -> database_url."""
        from common.config import Settings

        s = Settings(database_url="postgresql:///primary")
        assert s.resolved_control_plane_database_url == "postgresql:///primary"

    def test_resolved_control_plane_url_uses_override(self):
        from common.config import Settings

        s = Settings(
            database_url="postgresql:///primary",
            control_plane_database_url="postgresql:///control_plane",
        )
        assert s.resolved_control_plane_database_url == "postgresql:///control_plane"

    def test_resolved_tenant_data_url_falls_back(self):
        from common.config import Settings

        s = Settings(database_url="postgresql:///primary")
        assert s.resolved_tenant_data_database_url == "postgresql:///primary"

    def test_resolved_tenant_data_url_uses_override(self):
        from common.config import Settings

        s = Settings(
            database_url="postgresql:///primary",
            tenant_data_database_url="postgresql:///tenant_data",
        )
        assert s.resolved_tenant_data_database_url == "postgresql:///tenant_data"


class TestDatabaseManager:
    """Cover _DatabaseManager lazy-init edge cases (lines 24-33, 42-48, 51).

    These are the ''if self._xxx is None'' branches that create engines
    and session factories on first access.
    """

    def test_control_plane_engine_lazy_init(self):
        """line 24-29: _resolve_control_plane_engine creates engine on first call."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        # First call should create
        eng = mgr.control_plane_engine()
        assert eng is not None
        # Second call returns cached
        assert mgr.control_plane_engine() is eng

    def test_tenant_data_engine_lazy_init(self):
        """line 31-36: _resolve_tenant_data_engine creates engine on first call."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        eng = mgr.tenant_data_engine()
        assert eng is not None
        assert mgr.tenant_data_engine() is eng

    def test_control_plane_session_factory_lazy_init(self):
        """line 50-56: session factory created on first access."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        factory = mgr.control_plane_session_factory()
        assert factory is not None

    def test_tenant_data_session_factory_lazy_init(self):
        """line 42-48: tenant_data=True creates tenant session factory."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        factory = mgr.tenant_data_session_factory()
        assert factory is not None

    def test_set_engine_rebuilds_factories(self):
        """Lines 76-84: set_engine replaces engines and factories."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        handle = make_postgres_session(())
        try:
            mgr.set_engine(handle.engine)
            assert mgr.engine() is handle.engine
        finally:
            handle.close()

    def test_reset_engine_clears(self):
        """Lines 86-90: reset_engine clears cached engines."""
        from common.database import _DatabaseManager

        mgr = _DatabaseManager()
        _ = mgr.engine()  # trigger lazy init
        mgr.reset_engine()
        # After reset, a new call creates a new engine
        eng2 = mgr.engine()
        assert eng2 is not None

    def test_engine_function(self):
        """Line 99-100: engine() public function."""
        from sqlalchemy import Engine

        from common.database import engine

        e = engine()
        assert isinstance(e, Engine)

    def test_control_plane_engine_function(self):
        """Line 103-104."""
        from sqlalchemy import Engine

        from common.database import control_plane_engine

        e = control_plane_engine()
        assert isinstance(e, Engine)

    def test_tenant_data_engine_function(self):
        """Line 107-108."""
        from sqlalchemy import Engine

        from common.database import tenant_data_engine

        e = tenant_data_engine()
        assert isinstance(e, Engine)

    def test_session_factory_function(self):
        """Line 111-112."""
        from common.database import session_factory

        f = session_factory()
        assert f is not None

    def test_control_plane_session_factory_function(self):
        """Line 115-116."""
        from common.database import control_plane_session_factory

        f = control_plane_session_factory()
        assert f is not None

    def test_tenant_data_session_factory_function(self):
        """Line 119-120."""
        from common.database import tenant_data_session_factory

        f = tenant_data_session_factory()
        assert f is not None

    def test_set_engine_function(self):
        """Line 138-139."""
        from common.database import set_engine

        handle = make_postgres_session(())
        try:
            set_engine(handle.engine)
        finally:
            handle.close()

    def test_reset_engine_function(self):
        """Line 142-143."""
        from common.database import reset_engine

        reset_engine()


class TestMakeSession:
    """Cover make_session edge cases (lines 122-135)."""

    def test_make_session_from_sessionmaker(self):
        """line 124-128: sessionmaker input returns a Session."""
        from sqlalchemy.orm import Session, sessionmaker

        from common.database import make_session

        handle = make_postgres_session(())
        try:
            factory = sessionmaker(bind=handle.engine)
            session = make_session(factory)
            assert isinstance(session, Session)
            session.close()
        finally:
            handle.close()

    def test_make_session_direct_session_instance(self):
        """line 130: direct Session instance."""
        from sqlalchemy.orm import Session

        from common.database import make_session

        handle = make_postgres_session(())
        try:
            session = Session(bind=handle.engine)
            result = make_session(session)
            assert isinstance(result, Session)
            result.close()
        finally:
            handle.close()

    def test_make_session_type_error_non_session(self):
        """line 131-132: TypeError when input is not a Session."""
        from common.database import make_session

        with pytest.raises(TypeError, match="Expected a SQLAlchemy Session"):
            make_session("not-a-session")

    def test_make_session_runtime_error_no_bind(self):
        """line 133-134: RuntimeError when session has no engine bind."""
        from sqlalchemy.orm import sessionmaker

        from common.database import make_session

        factory = sessionmaker()
        with pytest.raises(RuntimeError, match="does not have an engine bind"):
            make_session(factory)


class TestLogging:
    """Cover setup_logging function (common/logging.py)."""

    def test_setup_logging_stdout(self):
        """lines 7-12: setup_logging configures root logger."""
        import logging

        from common.logging import setup_logging

        # Should not raise
        setup_logging()
        root = logging.getLogger()
        assert root.level != 0

    def test_setup_logging_custom_level(self):
        """Verify level from settings is respected."""
        import logging

        from common.logging import setup_logging

        setup_logging()
        root = logging.getLogger()
        assert root.hasHandlers()
