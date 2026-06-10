import os
import time

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from analytics.services.monthly_aggregation_service import MonthlyAggregationService
from auth.hashing import hash_password
from auth.schema import UserModel
from common.database import Base, init_db, reset_engine, set_engine
from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel
from ontology.schema import (
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
)
from tenant_data.base import TenantDataBase

_TEST_SERVER_URL = os.environ.get(
    "CANOPY_TEST_SERVER_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:5432",
)
_TEST_CONTROL_PLANE_DATABASE_NAME = os.environ.get(
    "CANOPY_TEST_CONTROL_PLANE_DATABASE_NAME",
    "canopy_test_control_plane",
)
_TEST_TENANT_DATA_DATABASE_NAME = os.environ.get(
    "CANOPY_TEST_TENANT_DATA_DATABASE_NAME",
    "canopy_test_tenant_data",
)
_TEST_SOURCE_DATABASE_NAME = os.environ.get(
    "CANOPY_TEST_SOURCE_DATABASE_NAME",
    "source_staging_test",
)

# When running with pytest-xdist, isolate each worker into its own database to avoid
# cross-test interference and Postgres TRUNCATE deadlocks.
_XDIST_WORKER = os.environ.get("PYTEST_XDIST_WORKER")
if _XDIST_WORKER:
    if "CANOPY_TEST_CONTROL_PLANE_DATABASE_NAME" not in os.environ:
        _TEST_CONTROL_PLANE_DATABASE_NAME = f"{_TEST_CONTROL_PLANE_DATABASE_NAME}_{_XDIST_WORKER}"
    if "CANOPY_TEST_TENANT_DATA_DATABASE_NAME" not in os.environ:
        _TEST_TENANT_DATA_DATABASE_NAME = f"{_TEST_TENANT_DATA_DATABASE_NAME}_{_XDIST_WORKER}"
    if "CANOPY_TEST_SOURCE_DATABASE_NAME" not in os.environ:
        _TEST_SOURCE_DATABASE_NAME = f"{_TEST_SOURCE_DATABASE_NAME}_{_XDIST_WORKER}"

_TEST_DATABASE_URL = f"{_TEST_SERVER_URL.rstrip('/')}/{_TEST_CONTROL_PLANE_DATABASE_NAME}"
_TEST_TENANT_DATA_URL = f"{_TEST_SERVER_URL.rstrip('/')}/{_TEST_TENANT_DATA_DATABASE_NAME}"
_TEST_SOURCE_URL = f"{_TEST_SERVER_URL.rstrip('/')}/{_TEST_SOURCE_DATABASE_NAME}"
_SNAPSHOT_ID = "test-snapshot-001"


@pytest.fixture(scope="session", autouse=True)
def _set_event_loop_policy():
    """Windows fix: psycopg requires SelectorEventLoop, not ProactorEventLoop."""
    import sys

    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: pure logic tests (no DB/network)")
    config.addinivalue_line("markers", "integration: tests using DB or network fixtures")
    config.addinivalue_line("markers", "business_rule: core business logic that must never regress")
    config.addinivalue_line("markers", "api_schema: API response contract and schema tests")
    config.addinivalue_line("markers", "smoke: end-to-end smoke tests")


_DB_FIXTURE_NAMES: frozenset[str] = frozenset(
    {
        # Control-plane DB
        "engine",
        "control_plane_engine",
        "db_session",
        # Tenant-data DB
        "tenant_data_engine",
        "td_engine",
        "td_session",
        # Source DB
        "source_engine",
        # API tests (almost always DB-backed)
        "client",
        "auth_headers",
        # Helpers that create dedicated postgres DBs for a module
        "make_postgres_session",
    }
)


def pytest_collection_modifyitems(config, items):
    needs_db = False
    for item in items:
        fspath = str(item.fspath)
        if "/tests/unit/" in fspath or "\\tests\\unit\\" in fspath:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in fspath or "\\tests\\integration\\" in fspath:
            item.add_marker(pytest.mark.integration)

        if not needs_db:
            # If any collected test requests a DB-ish fixture, enable DB init/cleanup.
            if _DB_FIXTURE_NAMES.intersection(getattr(item, "fixturenames", ())):
                needs_db = True

    # Used by autouse fixtures to avoid booting Postgres for pure-logic runs.
    setattr(config, "_canopy_needs_db", needs_db)


def _ensure_database_exists(database_url: str) -> None:
    url = make_url(database_url)
    admin_url = url.set(database="postgres")
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": url.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session")
def control_plane_engine():
    _ensure_database_exists(_TEST_DATABASE_URL)
    engine = create_engine(_TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def tenant_data_engine():
    _ensure_database_exists(_TEST_TENANT_DATA_URL)
    engine = create_engine(_TEST_TENANT_DATA_URL)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def source_engine():
    _ensure_database_exists(_TEST_SOURCE_URL)
    engine = create_engine(_TEST_SOURCE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def engine(control_plane_engine):
    return control_plane_engine


def _truncate_all_tables(db_engine, metadata) -> None:
    dialect = db_engine.dialect.name

    def _existing_tables(conn) -> set[tuple[str, str]]:
        if dialect == "postgresql":
            rows = conn.execute(
                text(
                    """
                    SELECT schemaname, tablename
                    FROM pg_tables
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                    """
                )
            ).all()
            return {(r[0], r[1]) for r in rows}

        # SQLite / others: no schemas. Treat schema as empty string.
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).all()
        return {("", r[0]) for r in rows}

    def _quote_ident(schema: str | None, name: str) -> str:
        # TRUNCATE does not accept bind params for identifiers.
        # Identifiers here are always from SQLAlchemy metadata / DB catalog, but still escape quotes.
        def esc(v: str) -> str:
            return v.replace('"', '""')

        if schema:
            return f'"{esc(schema)}"."{esc(name)}"'
        return f'"{esc(name)}"'

    max_attempts = 5
    base_sleep_s = 0.05

    for attempt in range(1, max_attempts + 1):
        try:
            with db_engine.begin() as conn:
                # Serialize cleanup within one database to avoid TRUNCATE deadlocks.
                if dialect == "postgresql":
                    conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('canopy_test_db_truncate'))"))

                existing = _existing_tables(conn)

                # In Postgres, the real set of tables can diverge from SQLAlchemy metadata
                # because tests may rely on search_path (schema-qualified tables) and optional
                # models. For teardown, truncate everything we can see in non-system schemas.
                if dialect == "postgresql":
                    idents = [_quote_ident(schema or None, name) for (schema, name) in existing]
                else:
                    if not metadata.sorted_tables:
                        return
                    idents = []
                    for table in metadata.sorted_tables:
                        schema = table.schema or ""
                        if (schema, table.name) in existing:
                            idents.append(_quote_ident(table.schema, table.name))

                if not idents:
                    return

                # Deterministic order => consistent lock acquisition.
                idents = sorted(set(idents))
                conn.execute(text(f"TRUNCATE TABLE {', '.join(idents)} RESTART IDENTITY CASCADE"))
            return
        except OperationalError as e:
            # psycopg deadlock/lock issues during parallel teardown.
            msg = str(getattr(e, "orig", e)).lower()
            if ("deadlock detected" in msg) or ("could not obtain lock" in msg) or ("lock timeout" in msg):
                if attempt == max_attempts:
                    raise
                time.sleep(base_sleep_s * (2 ** (attempt - 1)))
                continue
            raise


@pytest.fixture(scope="session")
def db_initialized(pytestconfig, control_plane_engine, tenant_data_engine):
    if not getattr(pytestconfig, "_canopy_needs_db", False):
        yield False
        return

    set_engine(control_plane_engine, tenant_data_engine)
    init_db()
    yield True
    reset_engine()


@pytest.fixture(autouse=True)
def _clean_db_after_test(pytestconfig, db_initialized, control_plane_engine, tenant_data_engine, request):
    # Skip all DB work for pure-logic tests (no DB fixtures requested).
    if not getattr(pytestconfig, "_canopy_needs_db", False):
        yield
        return

    # If this specific test doesn't request any DB-ish fixtures, skip truncation.
    if not _DB_FIXTURE_NAMES.intersection(getattr(request, "fixturenames", ())):
        yield
        return

    yield
    _truncate_all_tables(control_plane_engine, Base.metadata)
    _truncate_all_tables(tenant_data_engine, TenantDataBase.metadata)


@pytest.fixture
def db_session(db_initialized, control_plane_engine):
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=control_plane_engine)
    session = test_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_initialized):
    from app import create_app

    app = create_app()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def seed_user(db_session):
    user = UserModel(
        id="test-user-1",
        email="admin@canopy.dev",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def seed_tenant_and_membership(db_session, seed_user):
    """Create a tenant and membership so auth tokens carry tenant context."""
    tenant = TenantModel(
        id="test-tenant-1",
        tenant_uuid="tuuid-test-1",
        name="Test Tenant",
        slug="test-tenant",
        lifecycle_state="active",
        status="active",
    )
    db_session.add(tenant)
    membership = TenantMembershipModel(
        user_id=seed_user.id,
        tenant_id="test-tenant-1",
        role="admin",
        status="active",
    )
    db_session.add(membership)
    db_session.commit()
    return tenant, membership


@pytest.fixture
def auth_headers(client, seed_user, seed_tenant_and_membership):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@canopy.dev", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_departments(db_session):
    dept_ids = ["dept-1", "dept-2", "dept-3", "dept-4", "dept-5", "dept-6"]
    dept_names = ["Engineering", "Sales", "Marketing", "Operations", "Finance", "HR"]
    models = [
        DepartmentModel(
            id=did,
            snapshot_id=_SNAPSHOT_ID,
            source_department_key=f"src-{did}",
            source_lineage=f"source_snapshot:{_SNAPSHOT_ID}",
            name=name,
            status="active",
        )
        for did, name in zip(dept_ids, dept_names)
    ]
    db_session.add_all(models)
    return dept_ids, dept_names


def _seed_employees(db_session):
    employees = [
        ("emp-1", "dept-1", "Alice Chen"),
        ("emp-2", "dept-1", "Bob Martinez"),
        ("emp-3", "dept-1", "Carol Wu"),
        ("emp-10", "dept-2", "David Park"),
        ("emp-11", "dept-2", "Eva Johansson"),
        ("emp-20", "dept-3", "Frank Liu"),
        ("emp-21", "dept-3", "Grace Kim"),
    ]
    models = [
        EmployeeModel(
            id=eid,
            snapshot_id=_SNAPSHOT_ID,
            source_employee_key=f"src-{eid}",
            source_lineage=f"source_snapshot:{_SNAPSHOT_ID}",
            department_id=did,
            employee_code=eid.upper(),
            full_name=name,
            employment_status="active",
        )
        for eid, did, name in employees
    ]
    db_session.add_all(models)
    return employees


def _seed_payroll(db_session):
    months = [
        "2025-11",
        "2025-12",
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
    ]
    dept_monthly = {
        "dept-1": [420000, 425000, 422000, 428000, 430000, 435000, 440000],
        "dept-2": [310000, 312000, 308000, 315000, 320000, 322000, 325000],
        "dept-3": [230000, 228000, 232000, 235000, 238000, 240000, 242000],
        "dept-4": [180000, 181000, 179000, 182000, 184000, 185000, 187000],
        "dept-5": [155000, 154000, 156000, 157000, 158000, 160000, 162000],
        "dept-6": [129500, 130000, 128500, 131000, 132000, 133000, 134500],
    }
    dept_employee_map = {
        "dept-1": ["emp-1", "emp-2", "emp-3"],
        "dept-2": ["emp-10", "emp-11"],
        "dept-3": ["emp-20", "emp-21"],
        "dept-4": ["emp-1"],
        "dept-5": ["emp-1"],
        "dept-6": ["emp-1"],
    }

    models = []
    idx = 0
    for did, amounts in dept_monthly.items():
        emp_ids = dept_employee_map[did]
        for i, month in enumerate(months):
            for eid in emp_ids:
                split = round(amounts[i] / len(emp_ids), 2)
                models.append(
                    PayrollExpenseModel(
                        id=f"pay-{idx}",
                        snapshot_id=_SNAPSHOT_ID,
                        source_payroll_key=f"src-pay-{idx}",
                        source_lineage=f"source_snapshot:{_SNAPSHOT_ID}",
                        employee_id=eid,
                        department_id=did,
                        payroll_month=month,
                        amount=split,
                        currency="MYR",
                        is_resolved=True,
                    )
                )
                idx += 1
    db_session.add_all(models)


def _seed_claims(db_session):
    claim_templates = [
        ("claim-1", "dept-1", "emp-1", "Equipment", 2500.00, "2026-05-03"),
        ("claim-2", "dept-2", "emp-10", "Travel", 3200.00, "2026-05-05"),
        ("claim-3", "dept-3", "emp-20", "Travel", 4800.00, "2026-05-08"),
        ("claim-4", "dept-1", "emp-3", "Travel", 1800.00, "2026-05-10"),
        ("claim-5", "dept-2", "emp-11", "Meals", 350.00, "2026-05-12"),
        ("claim-6", "dept-3", "emp-21", "Office Supplies", 620.00, "2026-05-14"),
        ("claim-7", "dept-1", "emp-2", "Training", 1200.00, "2026-05-01"),
        ("claim-8", "dept-1", "emp-1", "Meals", 800.00, "2026-05-02"),
        ("claim-9", "dept-4", "emp-1", "Other", 500.00, "2026-05-06"),
    ]
    models = [
        ExpenseClaimModel(
            id=cid,
            snapshot_id=_SNAPSHOT_ID,
            source_claim_key=f"src-{cid}",
            source_lineage=f"source_snapshot:{_SNAPSHOT_ID}",
            employee_id=eid,
            department_id=did,
            claim_type=ctype,
            claim_date=date,
            amount=amount,
            currency="MYR",
            is_resolved=True,
        )
        for cid, did, eid, ctype, amount, date in claim_templates
    ]
    db_session.add_all(models)


@pytest.fixture
def seed_analytics_data(db_session):
    """Seed ontology data and run the aggregation pipeline."""
    _seed_departments(db_session)
    _seed_employees(db_session)
    _seed_payroll(db_session)
    _seed_claims(db_session)
    db_session.commit()

    MonthlyAggregationService(db_session).compute_monthly_spends(
        snapshot_id=_SNAPSHOT_ID,
        current_month="2026-05",
        previous_month="2026-04",
        anomaly_count=3,
    )

    return db_session
