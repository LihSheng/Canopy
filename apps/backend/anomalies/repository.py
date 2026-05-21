from sqlalchemy.orm import Session

from anomalies.domain import AnomalyOutput
from anomalies.schema import DetectedAnomalyModel


class AnomalyRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_anomalies(self, outputs: list[AnomalyOutput]) -> list[DetectedAnomalyModel]:
        models = [
            DetectedAnomalyModel(
                id=o.id,
                snapshot_id=o.snapshot_id,
                anomaly_type=o.anomaly_type,
                target_entity_type=o.target_entity_type,
                target_entity_id=o.target_entity_id,
                month_key=o.month_key,
                baseline_value=o.baseline_value,
                observed_value=o.observed_value,
                delta_value=o.delta_value,
                delta_percent=o.delta_percent,
                severity=o.severity,
                driver_payload_json=DetectedAnomalyModel.pack_drivers(o.driver_details),
            )
            for o in outputs
        ]
        self._db.add_all(models)
        self._db.commit()
        return models

    def find_all(self, snapshot_id: str | None = None) -> list[AnomalyOutput]:
        q = self._db.query(DetectedAnomalyModel)
        if snapshot_id:
            q = q.filter(DetectedAnomalyModel.snapshot_id == snapshot_id)
        models = q.order_by(DetectedAnomalyModel.severity.desc()).all()
        return [_model_to_domain(m) for m in models]

    def find_by_id(self, anomaly_id: str) -> AnomalyOutput | None:
        model = self._db.query(DetectedAnomalyModel).filter(DetectedAnomalyModel.id == anomaly_id).first()
        if model is None:
            return None
        return _model_to_domain(model)

    def count_for_snapshot(self, snapshot_id: str) -> int:
        return self._db.query(DetectedAnomalyModel).filter(DetectedAnomalyModel.snapshot_id == snapshot_id).count()

    def clear_snapshot(self, snapshot_id: str) -> None:
        self._db.query(DetectedAnomalyModel).filter(DetectedAnomalyModel.snapshot_id == snapshot_id).delete()
        self._db.commit()


def _model_to_domain(m: DetectedAnomalyModel) -> AnomalyOutput:
    return AnomalyOutput(
        id=m.id,
        snapshot_id=m.snapshot_id,
        anomaly_type=m.anomaly_type,
        target_entity_type=m.target_entity_type,
        target_entity_id=m.target_entity_id,
        month_key=m.month_key,
        baseline_value=m.baseline_value,
        observed_value=m.observed_value,
        delta_value=m.delta_value,
        delta_percent=m.delta_percent,
        severity=m.severity,
        driver_details=DetectedAnomalyModel.unpack_drivers(m.driver_payload_json),
    )
