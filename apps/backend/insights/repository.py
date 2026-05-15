from sqlalchemy.orm import Session

from insights.domain import InsightSummary
from insights.schema import GeneratedInsightModel


class InsightRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, summary: InsightSummary) -> GeneratedInsightModel:
        model = GeneratedInsightModel(
            id=summary.id,
            snapshot_id=summary.snapshot_id,
            current_month=summary.current_month,
            summary_text=summary.summary_text,
            recommendations_json=GeneratedInsightModel.pack_list(summary.recommendations),
            key_findings_json=GeneratedInsightModel.pack_list(summary.key_findings),
            is_fallback=summary.is_fallback,
            generated_at=summary.generated_at,
            anomaly_count=summary.anomaly_count,
            department_count=summary.department_count,
            total_payroll=summary.total_payroll,
            total_claims=summary.total_claims,
        )
        self._db.add(model)
        self._db.commit()
        return model

    def find_latest(self) -> InsightSummary | None:
        model = (
            self._db.query(GeneratedInsightModel)
            .order_by(GeneratedInsightModel.generated_at.desc())
            .first()
        )
        if model is None:
            return None
        return _model_to_domain(model)

    def find_by_snapshot(self, snapshot_id: str) -> InsightSummary | None:
        model = (
            self._db.query(GeneratedInsightModel)
            .filter(GeneratedInsightModel.snapshot_id == snapshot_id)
            .order_by(GeneratedInsightModel.generated_at.desc())
            .first()
        )
        if model is None:
            return None
        return _model_to_domain(model)

    def find_by_month(self, month: str) -> InsightSummary | None:
        model = (
            self._db.query(GeneratedInsightModel)
            .filter(GeneratedInsightModel.current_month == month)
            .order_by(GeneratedInsightModel.generated_at.desc())
            .first()
        )
        if model is None:
            return None
        return _model_to_domain(model)

    def clear_snapshot(self, snapshot_id: str) -> None:
        self._db.query(GeneratedInsightModel).filter(
            GeneratedInsightModel.snapshot_id == snapshot_id
        ).delete()
        self._db.commit()


def _model_to_domain(m: GeneratedInsightModel) -> InsightSummary:
    return InsightSummary(
        id=m.id,
        snapshot_id=m.snapshot_id,
        current_month=m.current_month,
        summary_text=m.summary_text,
        recommendations=GeneratedInsightModel.unpack_list(m.recommendations_json),
        key_findings=GeneratedInsightModel.unpack_list(m.key_findings_json),
        is_fallback=m.is_fallback,
        generated_at=m.generated_at,
        anomaly_count=m.anomaly_count,
        department_count=m.department_count,
        total_payroll=m.total_payroll,
        total_claims=m.total_claims,
    )
