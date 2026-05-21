import json
import uuid
from dataclasses import asdict

from ontology.domain import (
    ExpenseClaim,
    MappingContext,
    MappingResult,
    OntologyMapper,
    UnresolvedRecord,
)
from ontology.mappers.attribution import AttributionResolver
from sync.domain import SourceClaim


class ClaimMapper(OntologyMapper[SourceClaim, ExpenseClaim]):
    entity_type = "expense_claims"

    def __init__(self):
        self._attribution = AttributionResolver()

    def map(
        self,
        source_rows: list[SourceClaim],
        context: MappingContext,
    ) -> MappingResult[ExpenseClaim]:
        mapped: list[ExpenseClaim] = []
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

            cost_center_id = self._attribution.resolve_cost_center(context, employee_source_key=src.employee_key)

            is_resolved = department_id is not None

            if not is_resolved:
                unresolved.append(
                    UnresolvedRecord(
                        source_key=src.source_key,
                        entity_type=self.entity_type,
                        reason="unable to resolve department for claim",
                        source_data=asdict(src),
                    )
                )

            claim = ExpenseClaim(
                id=str(uuid.uuid4()),
                snapshot_id=context.snapshot_id,
                source_claim_key=src.source_key,
                source_lineage=lineage,
                employee_id=employee_id,
                department_id=department_id,
                cost_center_id=cost_center_id,
                budget_code_id=None,
                claim_type=src.claim_type,
                claim_date=str(src.submitted_at),
                amount=src.amount,
                currency=src.currency,
                is_resolved=is_resolved,
            )
            mapped.append(claim)

        return MappingResult(
            entity_type=self.entity_type,
            snapshot_id=context.snapshot_id,
            mapped=mapped,
            unresolved=unresolved,
        )
