from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from sync.domain import SourceClaim, SourceReader
from sync.readers._source_models import SourceClaimRow


class ClaimReader(SourceReader[SourceClaim]):
    entity_type = "claims"

    def read(self, source_db: Session) -> list[SourceClaim]:
        stmt = select(SourceClaimRow)
        rows = source_db.execute(stmt).scalars().all()
        return [
            SourceClaim(
                source_key=r.source_key,
                employee_key=r.employee_key,
                department_key=r.department_key,
                amount=r.amount,
                currency=r.currency,
                claim_type=r.claim_type,
                submitted_at=datetime.fromisoformat(r.submitted_at),
                status=r.status,
            )
            for r in rows
        ]
