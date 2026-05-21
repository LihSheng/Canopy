"""Cursor column auto-detection for incremental sync.

Given a list of column schemas from an external database, detect the best
candidate for use as an incremental cursor column.

Priority list:
    1. updated_at
    2. last_modified_at
    3. modified_at
    4. synced_at
    5. last_updated
    6. timestamp
    7. created_at (lowest priority — only if no better match)
"""

_CURSOR_CANDIDATES = [
    "updated_at",
    "last_modified_at",
    "modified_at",
    "synced_at",
    "last_updated",
    "timestamp",
    "created_at",
]

_TIMESTAMP_TYPES = {
    "timestamp",
    "timestamptz",
    "timestamp without time zone",
    "timestamp with time zone",
    "datetime",
    "date",
}


def detect_cursor_column(columns: list[dict]) -> str | None:
    """Return the best cursor column name from a list of column schemas.

    Each column must be a dict with at least ``"name"`` and ``"data_type"`` keys.
    Returns ``None`` when no eligible column is found.
    """
    column_names = {col["name"]: col.get("data_type", "").lower() for col in columns}

    for candidate in _CURSOR_CANDIDATES:
        if candidate in column_names:
            data_type = column_names[candidate]
            # Check if it's a timestamp-like type
            if any(ts_type in data_type for ts_type in _TIMESTAMP_TYPES):
                return candidate

    # Fallback: scan all columns for any timestamp type
    for col in columns:
        dtype = col.get("data_type", "").lower()
        if any(ts_type in dtype for ts_type in _TIMESTAMP_TYPES):
            return col["name"]

    return None
