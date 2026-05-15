# ruff: noqa: E501
from api.schemas.anomalies import AnomalyDetailResponse, AnomalyItem


def get_anomalies() -> list[AnomalyItem]:
    return [
        AnomalyItem(
            id="anom-1",
            department_id="dept-3",
            department_name="Marketing",
            period="2026-05",
            description="Marketing total spend increased 8.7% month-over-month, driven by campaign-related travel claims.",
            severity="high",
            change_pct=8.7,
        ),
        AnomalyItem(
            id="anom-2",
            department_id="dept-6",
            department_name="HR",
            period="2026-05",
            description="HR payroll spend rose 12.3% due to three new hires onboarded this month.",
            severity="medium",
            change_pct=12.3,
        ),
        AnomalyItem(
            id="anom-3",
            department_id="dept-2",
            department_name="Sales",
            period="2026-05",
            description="Sales claims spend dropped 15.2% compared to previous quarter average.",
            severity="low",
            change_pct=-15.2,
        ),
    ]


def get_anomaly(anomaly_id: str) -> AnomalyDetailResponse | None:
    lookup = {
        "anom-1": AnomalyDetailResponse(
            id="anom-1",
            department_id="dept-3",
            department_name="Marketing",
            period="2026-05",
            description="Marketing total spend increased 8.7% month-over-month, driven by campaign-related travel claims.",
            severity="high",
            change_pct=8.7,
            baseline_value=253000.00,
            observed_value=275000.00,
            delta_value=22000.00,
            delta_percent=8.7,
            driver_details=["Q2 product launch campaign", "Increased travel for client visits", "3 new agency contracts"],
        ),
        "anom-2": AnomalyDetailResponse(
            id="anom-2",
            department_id="dept-6",
            department_name="HR",
            period="2026-05",
            description="HR payroll spend rose 12.3% due to three new hires onboarded this month.",
            severity="medium",
            change_pct=12.3,
            baseline_value=142000.00,
            observed_value=159500.00,
            delta_value=17500.00,
            delta_percent=12.3,
            driver_details=["3 new full-time hires", "Annual salary adjustments applied"],
        ),
        "anom-3": AnomalyDetailResponse(
            id="anom-3",
            department_id="dept-2",
            department_name="Sales",
            period="2026-05",
            description="Sales claims spend dropped 15.2% compared to previous quarter average.",
            severity="low",
            change_pct=-15.2,
            baseline_value=82500.00,
            observed_value=70000.00,
            delta_value=-12500.00,
            delta_percent=-15.2,
            driver_details=["Reduced travel due to virtual client meetings", "Q1 conference expenses not repeated"],
        ),
    }
    return lookup.get(anomaly_id)
