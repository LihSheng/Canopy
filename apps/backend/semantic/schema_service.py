"""Dataset schema introspection for semantic mapping.

Hybrid strategy:
- DB-backed datasets (postgresql, mysql): adapter introspection via discover_tables.
- Static file datasets: sample inference from stored JSONL preview data.
"""

import logging

from sqlalchemy.orm import Session

from connection.database_adapter import get_adapter
from connection.repository import ConnectionRepository
from connection.secret_store import AesGcmSecretStore, decrypt_secret_value
from dataset.domain import DatasetVersion
from dataset.preview_service import read_dataset_preview
from dataset.repository import DatasetRepository, DatasetVersionRepository
from semantic.domain import SchemaColumn

logger = logging.getLogger(__name__)

# Mapping from Python runtime types to semantic primitive types
_PY_TYPE_MAP: dict[type, str] = {
    int: "integer",
    float: "number",
    bool: "boolean",
    str: "string",
}


def _infer_type_from_sample(values: list) -> str:
    """Infer primitive type from sample column values."""
    non_null = [v for v in values if v is not None]
    if not non_null:
        return "string"
    types_found: set[str] = set()
    for v in non_null:
        inferred = _PY_TYPE_MAP.get(type(v), "string")
        types_found.add(inferred)
    if len(types_found) == 1:
        return types_found.pop()
    # Merge integer into number if both present
    if "integer" in types_found and "number" in types_found:
        types_found.discard("integer")
    if len(types_found) == 1:
        return types_found.pop()
    return "string"


# Mapping from raw DB type strings to semantic primitive types
_DB_TYPE_MAP: dict[str, str] = {
    "int": "integer",
    "integer": "integer",
    "tinyint": "integer",
    "smallint": "integer",
    "mediumint": "integer",
    "bigint": "integer",
    "serial": "integer",
    "bigserial": "integer",
    "int2": "integer",
    "int4": "integer",
    "int8": "integer",
    "float": "number",
    "double": "number",
    "real": "number",
    "decimal": "number",
    "numeric": "number",
    "money": "number",
    "bool": "boolean",
    "boolean": "boolean",
    "character": "string",
    "char": "string",
    "varchar": "string",
    "text": "string",
    "mediumtext": "string",
    "longtext": "string",
    "blob": "string",
    "bytea": "string",
    "date": "date",
    "datetime": "datetime",
    "timestamp": "datetime",
    "timestamptz": "datetime",
    "time": "datetime",
    "year": "integer",
    "json": "string",
    "jsonb": "string",
    "uuid": "string",
}


def _normalize_db_type(raw: str) -> str:
    """Normalize a raw DB type string to a primitive type."""
    clean = raw.strip().lower().split("(")[0].split(" ")[0]
    return _DB_TYPE_MAP.get(clean, "string")


class DatasetSchemaService:
    """Provides schema (column names + primitive types) for dataset versions.

    Strategy:
    1. DB-backed (postgresql, mysql): introspect via the connection adapter's
       discover_tables to get native column types.
    2. Static file or fallback: read stored JSONL preview data and infer
       primitive types from sample values.
    """

    def __init__(self, db: Session):
        self._db = db
        self._dataset_repo = DatasetRepository(db)
        self._version_repo = DatasetVersionRepository(db)
        self._connection_repo = ConnectionRepository(db)

    async def get_schema(self, dataset_id: str, dataset_version_id: str) -> list[SchemaColumn] | None:
        """Get schema columns with primitive types for a dataset version."""
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            return None

        version = self._version_repo.get(dataset_version_id)
        if version is None:
            return None

        # Strategy 1: DB introspection for postgresql/mysql sources
        if dataset.connection_id:
            connection = self._connection_repo.get(dataset.connection_id)
            if connection and connection.source_type in ("postgresql", "mysql"):
                db_schema = await self._introspect_from_db(connection, dataset.source_object_name)
                if db_schema:
                    return db_schema
                logger.warning(
                    "DB schema introspection returned no results for dataset %s"
                    " (connection %s, source %s, table %s);"
                    " falling back to preview inference",
                    dataset_id,
                    dataset.connection_id,
                    connection.source_type,
                    dataset.source_object_name,
                )

        # Strategy 2: Infer from stored JSONL preview data (static file or fallback)
        return self._infer_from_preview(version)

    async def get_column_sample(self, dataset_id: str, dataset_version_id: str, column_name: str) -> list:
        """Get sample values for a specific column (used for PK validation)."""
        version = self._version_repo.get(dataset_version_id)
        if version is None:
            return []
        columns, rows = self._read_preview(version)
        if column_name not in columns:
            return []
        col_idx = columns.index(column_name)
        return [row[col_idx] if col_idx < len(row) else None for row in rows]

    async def _introspect_from_db(self, connection, source_object_name: str) -> list[SchemaColumn] | None:
        """Introspect table schema from a DB connection adapter."""
        try:
            adapter = get_adapter(connection.source_type)
            config = dict(connection.config_json or {})
            password = config.get("password")
            if password and isinstance(password, str):
                config["password"] = decrypt_secret_value(
                    password,
                    AesGcmSecretStore(),
                    allow_legacy_plaintext=True,
                )
            # discover_tables returns metadata for all user tables
            tables = await adapter.discover_tables(config)
            # Find the matching table by name
            for table in tables:
                if table.get("table_name", "").lower() == source_object_name.lower():
                    return [
                        SchemaColumn(
                            column_name=col["name"],
                            primitive_type=_normalize_db_type(col["data_type"]),
                        )
                        for col in table.get("columns", [])
                    ]
            logger.warning(
                "Table %s not found in discovery results for connection %s (source_type=%s); got %d tables",
                source_object_name,
                connection.id,
                connection.source_type,
                len(tables),
            )
            return None
        except Exception:
            logger.exception(
                "Failed to introspect DB schema for connection %s (source_type=%s, table=%s)",
                connection.id,
                connection.source_type,
                source_object_name,
            )
            return None

    def _read_preview(self, version: DatasetVersion) -> tuple[list[str], list[list]]:
        storage_path = getattr(version, "storage_path", "")
        if not storage_path:
            return [], []
        try:
            preview = read_dataset_preview(storage_path, page=1, page_size=100)
            return preview.get("columns", []), preview.get("rows", [])
        except Exception:
            return [], []

    def _infer_from_preview(self, version: DatasetVersion) -> list[SchemaColumn]:
        """Infer schema from stored JSONL preview data."""
        columns, rows = self._read_preview(version)
        result: list[SchemaColumn] = []
        for col_idx, col_name in enumerate(columns):
            sample = [row[col_idx] if col_idx < len(row) else None for row in rows]
            inferred = _infer_type_from_sample(sample)
            result.append(SchemaColumn(column_name=col_name, primitive_type=inferred))
        return result
