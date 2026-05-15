import json
import uuid
from dataclasses import asdict

from ontology.domain import (
    MappingContext,
    MappingResult,
    OntologyMapper,
    PayrollExpense,
    UnresolvedRecord,
)
from ontology.mappers.attribution import AttributionResolver
from sync.domain import SourcePayroll


class PayrollMapper(OntologyMapper[SourcePayroll, PayrollExpense]):
    entity_type = "payroll_expenses"

    def __init__(self):
        self._attribution = AttributionResolver()

    def map(
        self,
        source_rows: list[SourcePayroll],
        context: MappingContext,
    ) -> MappingResult[PayrollExpense]:
        mapped: list[PayrollExpense] = []
        unresolved: list[UnresolvedRecord] = []

        for src in source_rows:
            lineage = json.dumps(asdict(src), default=str)

            employee_id = ""
            if src.employee_key in context.employees:
                employee_id = context.employees[src.employee_key].id
            else:
                unresolved.append(
                    UnresolvedRecord(
                        source_key=src.source_key,
                        entity_type=self.entity_type,
                        reason=f"employee {src.employee_key} not found",
                        source_data=asdict(src),
                    )
                )
                continue

            department_id = self._attribution.resolve_department(
                context,
                direct_department_key=src.department_key,
                employee_source_key=src.employee_key,
                cost_center_source_key=None,
            )

            cost_center_id = self._attribution.resolve_cost_center(
                context, employee_source_key=src.employee_key
            )

            is_resolved = department_id is not None

            if not is_resolved:
                unresolved.append(
                    UnresolvedRecord(
                        source_key=src.source_key,
                        entity_type=self.entity_type,
                        reason=f"unable to resolve department for payroll",
                        source_data=asdict(src),
                    )
                )

            pe = PayrollExpense(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_payroll_key=src.source_key,
                source_lineage=lineage,
                employee_id=employee_id,
                department_id=department_id,
                cost_center_id=cost_center_id,
                budget_code_id=None,
                payroll_month=src.period_start[:7] if len(src.period_start) >= 7 else src.period_start,
                amount=src.amount,
                currency=src.currency,
                pay_component="base_salary",
                is_resolved=is_resolved,
            )
            mapped.append(pe)

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )
