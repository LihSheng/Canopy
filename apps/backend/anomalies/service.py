from sqlalchemy.orm import Session

from analytics.service import (
    get_department_map,
    get_monthly_spends_for_month,
)
from anomalies.domain import AnomalyOutput
from anomalies.repository import AnomalyRepository
from anomalies.rules import department_claim_spike_rule, department_total_spike_rule


def detect_anomalies(
    db: Session,
    snapshot_id: str,
    current_month: str,
    previous_month: str,
) -> list[AnomalyOutput]:
    anomaly_repo = AnomalyRepository(db)
    anomaly_repo.clear_snapshot(snapshot_id)

    current_spends = get_monthly_spends_for_month(db, current_month, snapshot_id=snapshot_id)
    previous_spends = get_monthly_spends_for_month(db, previous_month, snapshot_id=snapshot_id)

    outputs: list[AnomalyOutput] = []
    outputs.extend(department_total_spike_rule(snapshot_id, current_spends, previous_spends))
    outputs.extend(department_claim_spike_rule(snapshot_id, current_spends, previous_spends))

    anomaly_repo.save_anomalies(outputs)
    return outputs


def get_anomalies_list(
    db: Session,
    department_id: str | None = None,
    snapshot_id: str | None = None,
) -> list[dict]:
    repo = AnomalyRepository(db)
    outputs = repo.find_all(snapshot_id=snapshot_id)
    if department_id:
        outputs = [o for o in outputs if o.target_entity_id == department_id]
    dept_map = get_department_map(db, snapshot_id=snapshot_id)
    return [_to_item(o, dept_map) for o in outputs]


def get_anomaly_detail(db: Session, anomaly_id: str) -> dict | None:
    repo = AnomalyRepository(db)
    output = repo.find_by_id(anomaly_id)
    if output is None:
        return None
    dept_map = get_department_map(db)
    return _to_detail(output, dept_map)


def _to_item(o: AnomalyOutput, dept_map: dict[str, str]) -> dict:
    return {
        "id": o.id,
        "department_id": o.target_entity_id,
        "department_name": dept_map.get(o.target_entity_id, o.target_entity_id),
        "period": o.month_key,
        "description": o.description,
        "severity": o.severity,
        "change_pct": o.delta_percent,
    }


def _to_detail(o: AnomalyOutput, dept_map: dict[str, str]) -> dict:
    return {
        "id": o.id,
        "department_id": o.target_entity_id,
        "department_name": dept_map.get(o.target_entity_id, o.target_entity_id),
        "period": o.month_key,
        "description": o.description,
        "severity": o.severity,
        "change_pct": o.delta_percent,
        "baseline_value": o.baseline_value,
        "observed_value": o.observed_value,
        "delta_value": o.delta_value,
        "delta_percent": o.delta_percent,
        "driver_details": o.driver_details,
    }
