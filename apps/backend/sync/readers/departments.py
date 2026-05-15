from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourceDepartment, SourceReader
from sync.readers._source_models import SourceDepartmentRow


class DepartmentReader(SourceReader[SourceDepartment]):
    entity_type = "departments"

    def read(self, source_db: Session) -> list[SourceDepartment]:
        stmt = select(SourceDepartmentRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourceDepartment(
                source_key=r.source_key,
                name=r.name,
                parent_key=r.parent_key,
                status=r.status,
            )
            for r in rows
        ]
