from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourceBudgetCode, SourceReader
from sync.readers._source_models import SourceBudgetCodeRow


class BudgetCodeReader(SourceReader[SourceBudgetCode]):
    entity_type = "budget_codes"

    def read(self, source_db: Session) -> list[SourceBudgetCode]:
        stmt = select(SourceBudgetCodeRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourceBudgetCode(
                source_key=r.source_key,
                name=r.name,
                department_key=r.department_key,
            )
            for r in rows
        ]
