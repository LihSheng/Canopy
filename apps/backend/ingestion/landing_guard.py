"""Landing-zone preservation guard.

Enforces the ELT boundary at ingestion: transformation-oriented keys
are rejected at landing stage so that raw data remains immutable.
"""

from common.errors import IngestionTransformNotAllowedError

_BLOCKED_INGESTION_KEYS: frozenset[str] = frozenset(
    {
        "transformations",
        "cleaning_steps",
        "column_mappings",
        "rename_columns",
        "drop_columns",
        "cast_rules",
        "filters",
        "masking_rules",
        "normalization_rules",
    }
)


def blocked_ingestion_keys() -> frozenset[str]:
    return _BLOCKED_INGESTION_KEYS


def reject_transform_keys(payload: dict, label: str = "payload") -> None:
    """Raise IngestionTransformNotAllowedError if *payload* contains any blocked key.

    Checks top-level keys and also recurses one level into dict-valued keys
    (such as ``config_json``) so that transformation settings cannot be
    smuggled inside nested objects.
    """
    if not isinstance(payload, dict):
        return

    violations: list[str] = []

    # top-level keys
    for key in payload:
        if key in _BLOCKED_INGESTION_KEYS:
            violations.append(key)

    # one level deep — catches keys nested in config_json or similar
    for key, value in payload.items():
        if isinstance(value, dict):
            for nested_key in value:
                if nested_key in _BLOCKED_INGESTION_KEYS:
                    violations.append(f"{key}.{nested_key}")

    if violations:
        raise IngestionTransformNotAllowedError(blocked_keys=violations)
