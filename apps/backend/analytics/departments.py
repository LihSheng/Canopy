# ruff: noqa: E501
from api.schemas.dashboard import MonthlyTrendItem
from api.schemas.departments import (
    ClaimDetailItem,
    DepartmentClaimTypeItem,
    DepartmentDetailResponse,
    DepartmentItem,
    EmployeeContributionItem,
)

_sample_departments: list[dict] = [
    {"id": "dept-1", "name": "Engineering", "payroll_spend": 420000.00, "claims_spend": 65000.00, "total_spend": 485000.00, "change_pct": 3.2, "employee_count": 45},
    {"id": "dept-2", "name": "Sales", "payroll_spend": 310000.00, "claims_spend": 70000.00, "total_spend": 380000.00, "change_pct": -1.5, "employee_count": 32},
    {"id": "dept-3", "name": "Marketing", "payroll_spend": 230000.00, "claims_spend": 45000.00, "total_spend": 275000.00, "change_pct": 8.7, "employee_count": 18},
    {"id": "dept-4", "name": "Operations", "payroll_spend": 180000.00, "claims_spend": 30000.00, "total_spend": 210000.00, "change_pct": 1.1, "employee_count": 22},
    {"id": "dept-5", "name": "Finance", "payroll_spend": 155000.00, "claims_spend": 27350.50, "total_spend": 182350.50, "change_pct": -0.8, "employee_count": 14},
    {"id": "dept-6", "name": "HR", "payroll_spend": 129500.00, "claims_spend": 30000.00, "total_spend": 159500.00, "change_pct": 12.3, "employee_count": 10},
]

_employee_data: dict[str, list[dict]] = {
    "dept-1": [
        {"id": "emp-1", "name": "Alice Chen", "department": "Engineering", "payroll": 18500.00, "claims": 3200.00, "total": 21700.00},
        {"id": "emp-2", "name": "Bob Martinez", "department": "Engineering", "payroll": 17200.00, "claims": 1800.00, "total": 19000.00},
        {"id": "emp-3", "name": "Carol Wu", "department": "Engineering", "payroll": 16500.00, "claims": 4500.00, "total": 21000.00},
    ],
    "dept-2": [
        {"id": "emp-10", "name": "David Park", "department": "Sales", "payroll": 15200.00, "claims": 5200.00, "total": 20400.00},
        {"id": "emp-11", "name": "Eva Johansson", "department": "Sales", "payroll": 14800.00, "claims": 3800.00, "total": 18600.00},
    ],
    "dept-3": [
        {"id": "emp-20", "name": "Frank Liu", "department": "Marketing", "payroll": 16200.00, "claims": 6100.00, "total": 22300.00},
        {"id": "emp-21", "name": "Grace Kim", "department": "Marketing", "payroll": 15500.00, "claims": 2800.00, "total": 18300.00},
    ],
}

_dept_claim_types: dict[str, list[dict]] = {
    "dept-1": [{"type": "Equipment", "amount": 28500.00, "count": 12}, {"type": "Travel", "amount": 18500.00, "count": 28}, {"type": "Training", "amount": 12000.00, "count": 8}, {"type": "Meals", "amount": 6000.00, "count": 45}],
    "dept-2": [{"type": "Travel", "amount": 35000.00, "count": 52}, {"type": "Meals", "amount": 22000.00, "count": 95}, {"type": "Other", "amount": 13000.00, "count": 18}],
    "dept-3": [{"type": "Travel", "amount": 22000.00, "count": 35}, {"type": "Office Supplies", "amount": 12000.00, "count": 14}, {"type": "Meals", "amount": 11000.00, "count": 40}],
}

_claims_data: list[dict] = [
    {"id": "claim-1", "employee_name": "Alice Chen", "department": "Engineering", "type": "Equipment", "amount": 2500.00, "date": "2026-05-03"},
    {"id": "claim-2", "employee_name": "David Park", "department": "Sales", "type": "Travel", "amount": 3200.00, "date": "2026-05-05"},
    {"id": "claim-3", "employee_name": "Frank Liu", "department": "Marketing", "type": "Travel", "amount": 4800.00, "date": "2026-05-08"},
    {"id": "claim-4", "employee_name": "Carol Wu", "department": "Engineering", "type": "Travel", "amount": 1800.00, "date": "2026-05-10"},
    {"id": "claim-5", "employee_name": "Eva Johansson", "department": "Sales", "type": "Meals", "amount": 350.00, "date": "2026-05-12"},
    {"id": "claim-6", "employee_name": "Grace Kim", "department": "Marketing", "type": "Office Supplies", "amount": 620.00, "date": "2026-05-14"},
]


def get_departments() -> list[DepartmentItem]:
    return [
        DepartmentItem(
            id=d["id"], name=d["name"], total_spend=d["total_spend"],
            payroll_spend=d["payroll_spend"], claims_spend=d["claims_spend"], change_pct=d["change_pct"],
        )
        for d in _sample_departments
    ]


def get_department(department_id: str) -> DepartmentDetailResponse | None:
    for d in _sample_departments:
        if d["id"] == department_id:
            return DepartmentDetailResponse(
                id=d["id"], name=d["name"], payroll_spend=d["payroll_spend"],
                claims_spend=d["claims_spend"], total_spend=d["total_spend"],
                change_pct=d["change_pct"], employee_count=d["employee_count"],
            )
    return None


def get_department_employees(department_id: str) -> list[EmployeeContributionItem]:
    rows = _employee_data.get(department_id, [])
    return [EmployeeContributionItem(**r) for r in rows]


def get_department_trends(department_id: str) -> list[MonthlyTrendItem]:
    dept = next((d for d in _sample_departments if d["id"] == department_id), None)
    if dept is None:
        return []
    ratio = dept["total_spend"] / 1532350.50
    return [
        MonthlyTrendItem(month="2025-11", payroll=round(1180000.00 * ratio, 2), claims=round(265000.00 * ratio, 2), total=round(1445000.00 * ratio, 2)),
        MonthlyTrendItem(month="2025-12", payroll=round(1210000.00 * ratio, 2), claims=round(272000.00 * ratio, 2), total=round(1482000.00 * ratio, 2)),
        MonthlyTrendItem(month="2026-01", payroll=round(1195000.00 * ratio, 2), claims=round(258000.00 * ratio, 2), total=round(1453000.00 * ratio, 2)),
        MonthlyTrendItem(month="2026-02", payroll=round(1205000.00 * ratio, 2), claims=round(275000.00 * ratio, 2), total=round(1480000.00 * ratio, 2)),
        MonthlyTrendItem(month="2026-03", payroll=round(1220000.00 * ratio, 2), claims=round(280000.00 * ratio, 2), total=round(1500000.00 * ratio, 2)),
        MonthlyTrendItem(month="2026-04", payroll=round(1235000.00 * ratio, 2), claims=round(283000.00 * ratio, 2), total=round(1518000.00 * ratio, 2)),
        MonthlyTrendItem(month="2026-05", payroll=round(dept["payroll_spend"], 2), claims=round(dept["claims_spend"], 2), total=round(dept["total_spend"], 2)),
    ]


def get_department_claim_types(department_id: str) -> list[DepartmentClaimTypeItem]:
    rows = _dept_claim_types.get(department_id, [])
    return [DepartmentClaimTypeItem(**r) for r in rows]


_dept_name_by_id = {d["id"]: d["name"] for d in _sample_departments}


def get_claims(department_id: str | None = None) -> list[ClaimDetailItem]:
    if department_id:
        dept_name = _dept_name_by_id.get(department_id)
        filtered = [c for c in _claims_data if dept_name and c["department"] == dept_name]
        return [ClaimDetailItem(**c) for c in filtered]
    return [ClaimDetailItem(**c) for c in _claims_data]
