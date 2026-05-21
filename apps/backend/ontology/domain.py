from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Ontology domain types — snapshot-scoped business objects
# ---------------------------------------------------------------------------


@dataclass
class Department:
    id: str
    snapshot_id: str
    source_department_key: str
    source_lineage: str
    name: str
    parent_department_id: str | None = None
    status: str = "active"


@dataclass
class Employee:
    id: str
    snapshot_id: str
    source_employee_key: str
    source_lineage: str
    department_id: str
    cost_center_id: str | None = None
    employee_code: str = ""
    full_name: str = ""
    employment_status: str = "active"


@dataclass
class CostCenter:
    id: str
    snapshot_id: str
    source_cost_center_key: str
    source_lineage: str
    code: str
    name: str


@dataclass
class BudgetCode:
    id: str
    snapshot_id: str
    source_budget_code_key: str
    source_lineage: str
    code: str
    name: str
    category: str = ""


@dataclass
class ExpenseClaim:
    id: str
    snapshot_id: str
    source_claim_key: str
    source_lineage: str
    employee_id: str
    department_id: str | None = None
    cost_center_id: str | None = None
    budget_code_id: str | None = None
    claim_type: str = ""
    claim_date: str = ""
    amount: float = 0.0
    currency: str = "MYR"
    is_resolved: bool = True


@dataclass
class PayrollExpense:
    id: str
    snapshot_id: str
    source_payroll_key: str
    source_lineage: str
    employee_id: str
    department_id: str | None = None
    cost_center_id: str | None = None
    budget_code_id: str | None = None
    payroll_month: str = ""
    amount: float = 0.0
    currency: str = "MYR"
    pay_component: str = ""
    is_resolved: bool = True


# ---------------------------------------------------------------------------
# Mapping result types
# ---------------------------------------------------------------------------


@dataclass
class UnresolvedRecord:
    source_key: str
    entity_type: str
    reason: str
    source_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class MappingResult[T]:
    entity_type: str
    snapshot_id: str
    mapped: list[T] = field(default_factory=list)
    unresolved: list[UnresolvedRecord] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Mapping context — cross-entity references for attribution
# ---------------------------------------------------------------------------


@dataclass
class MappingContext:
    snapshot_id: str
    departments: dict[str, Department] = field(default_factory=dict)
    employees: dict[str, Employee] = field(default_factory=dict)
    cost_centers: dict[str, CostCenter] = field(default_factory=dict)
    budget_codes: dict[str, BudgetCode] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mapper contracts
# ---------------------------------------------------------------------------


class OntologyMapper[TIn, TOut](ABC):
    entity_type: str

    @abstractmethod
    def map(self, source_rows: list[TIn], context: MappingContext) -> MappingResult[TOut]: ...
