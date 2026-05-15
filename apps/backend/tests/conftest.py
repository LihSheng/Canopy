import pytest
from sqlalchemy import create_engine


def pytest_configure(config):
    config.addinivalue_line("markers", "unit: pure logic tests (no DB/network)")
    config.addinivalue_line("markers", "integration: tests using DB or network fixtures")
    config.addinivalue_line("markers", "business_rule: core business logic that must never regress")
    config.addinivalue_line("markers", "api_schema: API response contract and schema tests")
    config.addinivalue_line("markers", "smoke: end-to-end smoke tests")


def pytest_collection_modifyitems(config, items):
    for item in items:
        fspath = str(item.fspath)
        if "/tests/unit/" in fspath or "\\tests\\unit\\" in fspath:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in fspath or "\\tests\\integration\\" in fspath:
            item.add_marker(pytest.mark.integration)

from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from auth.hashing import hash_password
from auth.schema import UserModel
from common.database import Base, init_db, reset_engine, set_engine
from ontology.schema import (
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
)
from analytics.services.builder import run_aggregation_pipeline

_TEST_DATABASE_URL = "sqlite:///:memory:"
_SNAPSHOT_ID = "test-snapshot-001"


@pytest.fixture
def engine():
    engine = create_engine(
        _TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine


@pytest.fixture(autouse=True)
def _setup_db(engine):
    set_engine(engine)
    init_db(engine_override=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    reset_engine()


@pytest.fixture
def db_session(engine):
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = test_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    from app import create_app

    app = create_app()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def seed_user(db_session):
    user = UserModel(
        id="test-user-1",
        email="admin@herd.example",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, seed_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@herd.example", "password": "admin123"},
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
        "2025-11", "2025-12", "2026-01", "2026-02",
        "2026-03", "2026-04", "2026-05",
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
            for j, eid in enumerate(emp_ids):
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

    run_aggregation_pipeline(
        db=db_session,
        snapshot_id=_SNAPSHOT_ID,
        current_month="2026-05",
        previous_month="2026-04",
        anomaly_count=3,
    )

    return db_session
