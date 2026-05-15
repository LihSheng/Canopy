ANOMALY_THRESHOLDS: dict[str, float] = {
    "high_threshold_pct": 15.0,
    "medium_threshold_pct": 7.5,
}


def classify_severity(
    delta_percent: float,
    thresholds: dict[str, float] | None = None,
) -> str:
    t = thresholds or ANOMALY_THRESHOLDS
    high = t.get("high_threshold_pct", 15.0)
    medium = t.get("medium_threshold_pct", 7.5)

    if abs(delta_percent) >= high:
        return "high"
    if abs(delta_percent) >= medium:
        return "medium"
    return "low"
