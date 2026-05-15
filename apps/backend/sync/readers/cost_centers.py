from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourceCostCenter, SourceReader
from sync.readers._source_models import SourceCostCenterRow


class CostCenterReader(SourceReader[SourceCostCenter]):
    entity_type = "cost_centers"

    def read(self, source_db: Session) -> list[SourceCostCenter]:
        stmt = select(SourceCostCenterRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourceCostCenter(
                source_key=r.source_key,
                name=r.name,
                department_key=r.department_key,
            )
            for r in rows
        ]
