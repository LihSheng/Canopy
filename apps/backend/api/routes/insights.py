from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies.auth import get_current_user
from api.schemas.auth import SessionUser
from api.schemas.insights import InsightItem
from common.database import get_db
from common.errors import NotFoundError
from insights.service import get_latest_insight

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
def list_insights(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    insight = get_latest_insight(db)
    if insight is None:
        return []
    return [_to_item(insight)]


@router.get("/latest")
def latest_insight(
    db: Session = Depends(get_db),
    current_user: SessionUser = Depends(get_current_user),
):
    insight = get_latest_insight(db)
    if insight is None:
        raise NotFoundError("No insight available")
    return _to_item(insight)


def _to_item(insight) -> InsightItem:
    return InsightItem(
        id=insight.id,
        snapshot_id=insight.snapshot_id,
        current_month=insight.current_month,
        summary_text=insight.summary_text,
        recommendations=insight.recommendations,
        key_findings=insight.key_findings,
        is_fallback=insight.is_fallback,
        generated_at=insight.generated_at,
        anomaly_count=insight.anomaly_count,
        department_count=insight.department_count,
        total_payroll=insight.total_payroll,
        total_claims=insight.total_claims,
    )
