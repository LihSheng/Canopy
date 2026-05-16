from dataclasses import dataclass


@dataclass(frozen=True)
class ExportPreset:
    key: str
    label: str
    include_departments: bool
    include_anomalies: bool


EXPORT_PRESETS: dict[str, ExportPreset] = {
    "executive_summary": ExportPreset(
        key="executive_summary",
        label="Executive Summary",
        include_departments=True,
        include_anomalies=True,
    ),
    "department_spend": ExportPreset(
        key="department_spend",
        label="Department Spend",
        include_departments=True,
        include_anomalies=False,
    ),
    "anomaly_review": ExportPreset(
        key="anomaly_review",
        label="Anomaly Review",
        include_departments=False,
        include_anomalies=True,
    ),
}

EXPORT_PRESETS_BY_LABEL = {
    preset.label.lower(): preset for preset in EXPORT_PRESETS.values()
}


def resolve_export_preset(raw_preset: str | None) -> ExportPreset:
    if not raw_preset:
        return EXPORT_PRESETS["executive_summary"]

    normalized = raw_preset.strip().lower()
    return (
        EXPORT_PRESETS.get(normalized)
        or EXPORT_PRESETS_BY_LABEL.get(normalized)
        or EXPORT_PRESETS["executive_summary"]
    )
