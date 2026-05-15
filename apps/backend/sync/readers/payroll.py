from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourcePayroll, SourceReader
from sync.readers._source_models import SourcePayrollRow


class PayrollReader(SourceReader[SourcePayroll]):
    entity_type = "payroll"

    def read(self, source_db: Session) -> list[SourcePayroll]:
        stmt = select(SourcePayrollRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourcePayroll(
                source_key=r.source_key,
                employee_key=r.employee_key,
                department_key=r.department_key,
                amount=r.amount,
                currency=r.currency,
                period_start=r.period_start,
                period_end=r.period_end,
            )
            for r in rows
        ]
