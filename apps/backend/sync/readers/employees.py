from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourceEmployee, SourceReader
from sync.readers._source_models import SourceEmployeeRow


class EmployeeReader(SourceReader[SourceEmployee]):
    entity_type = "employees"

    def read(self, source_db: Session) -> list[SourceEmployee]:
        stmt = select(SourceEmployeeRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourceEmployee(
                source_key=r.source_key,
                full_name=r.full_name,
                department_key=r.department_key,
                cost_center_key=r.cost_center_key,
            )
            for r in rows
        ]
