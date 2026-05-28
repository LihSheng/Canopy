"""Schema drift domain types and classification logic."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class DriftType(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    RENAMED = "renamed"
    TYPE_CHANGE = "type_change"


class DriftSeverity(StrEnum):
    BREAKING = "breaking"
    NON_BREAKING = "non_breaking"


@dataclass
class ColumnSchema:
    """Normalized representation of a single column's schema."""

    name: str
    data_type: str  # normalized base type (e.g. "integer", "varchar", "timestamptz")
    nullable: bool = True
    char_max_length: int | None = None  # for string types
    numeric_precision: int | None = None  # for numeric/decimal types
    numeric_scale: int | None = None  # for numeric/decimal types
    datetime_precision: int | None = None  # for time types (0 = no tz, 1 = with tz for simplified)

    def to_dict(self) -> dict:
        d: dict[str, Any] = {
            "name": self.name,
            "data_type": self.data_type,
            "nullable": self.nullable,
        }
        if self.char_max_length is not None:
            d["char_max_length"] = self.char_max_length
        if self.numeric_precision is not None:
            d["numeric_precision"] = self.numeric_precision
        if self.numeric_scale is not None:
            d["numeric_scale"] = self.numeric_scale
        if self.datetime_precision is not None:
            d["datetime_precision"] = self.datetime_precision
        return d

    @classmethod
    def from_raw(cls, name: str, data_type: str, **extra: Any) -> "ColumnSchema":
        """Build a normalized ColumnSchema from raw adapter column info.

        ``extra`` may contain:
            - nullable (bool)
            - char_max_length (int)
            - numeric_precision (int)
            - numeric_scale (int)
            - datetime_precision (int)
        """
        return cls(
            name=name,
            data_type=normalize_type(data_type),
            nullable=bool(extra.get("nullable", True)),
            char_max_length=extra.get("char_max_length"),
            numeric_precision=extra.get("numeric_precision"),
            numeric_scale=extra.get("numeric_scale"),
            datetime_precision=extra.get("datetime_precision"),
        )


@dataclass
class DriftDelta:
    """Computed diff between two schemas."""

    added: list[ColumnSchema] = field(default_factory=list)
    removed: list[ColumnSchema] = field(default_factory=list)
    renamed: list[tuple[ColumnSchema, ColumnSchema]] = field(default_factory=list)  # (old, new)
    type_changed: list[tuple[ColumnSchema, ColumnSchema]] = field(default_factory=list)  # (old, new)

    @property
    def is_breaking(self) -> bool:
        return bool(self.removed or self.renamed or self.type_changed)

    @property
    def severity(self) -> DriftSeverity:
        return DriftSeverity.BREAKING if self.is_breaking else DriftSeverity.NON_BREAKING

    def to_dict(self) -> dict:
        return {
            "added": [c.to_dict() for c in self.added],
            "removed": [c.to_dict() for c in self.removed],
            "renamed": [{"old": o.to_dict(), "new": n.to_dict()} for o, n in self.renamed],
            "type_changed": [{"old": o.to_dict(), "new": n.to_dict()} for o, n in self.type_changed],
            "is_breaking": self.is_breaking,
            "severity": self.severity.value,
        }


@dataclass
class SchemaSignature:
    """Stored schema signature for a source object."""

    connection_id: str
    source_object_name: str
    columns: list[ColumnSchema]
    signature_hash: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def compute_hash(self) -> str:
        """Deterministic hash of the canonical column schema (order-independent)."""
        sorted_cols = sorted([json.dumps(c.to_dict(), sort_keys=True, default=str) for c in self.columns])
        raw = "\n".join(sorted_cols)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class SchemaDriftEvent:
    """Immutable record of a schema drift detection."""

    connection_id: str
    source_object_name: str
    dataset_id: str | None = None
    drift_type: str = ""  # "detected" for v1, can be more specific later
    before_hash: str = ""
    after_hash: str = ""
    before_columns: list[ColumnSchema] = field(default_factory=list)
    after_columns: list[ColumnSchema] = field(default_factory=list)
    delta: DriftDelta | None = None
    detected_by: str = "discovery"  # "discovery" or "sync"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "connection_id": self.connection_id,
            "source_object_name": self.source_object_name,
            "dataset_id": self.dataset_id,
            "drift_type": self.drift_type,
            "before_hash": self.before_hash,
            "after_hash": self.after_hash,
            "before_columns": [c.to_dict() for c in self.before_columns],
            "after_columns": [c.to_dict() for c in self.after_columns],
            "delta": self.delta.to_dict() if self.delta else None,
            "detected_by": self.detected_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ── Type normalization ────────────────────────────────────────────────

_TYPE_NORMALIZATION: dict[str, str] = {
    # PostgreSQL types
    "int2": "integer",
    "int4": "integer",
    "int8": "integer",
    "integer": "integer",
    "smallint": "integer",
    "bigint": "integer",
    "serial": "integer",
    "bigserial": "integer",
    "smallserial": "integer",
    "real": "float",
    "float4": "float",
    "float8": "float",
    "double precision": "float",
    "numeric": "numeric",
    "decimal": "numeric",
    "money": "money",
    "boolean": "boolean",
    "bool": "boolean",
    "text": "text",
    "character varying": "varchar",
    "varchar": "varchar",
    "char": "char",
    "character": "char",
    "timestamp": "timestamp",
    "timestamptz": "timestamptz",
    "timestamp with time zone": "timestamptz",
    "timestamp without time zone": "timestamp",
    "date": "date",
    "time": "time",
    "timetz": "timetz",
    "time with time zone": "timetz",
    "time without time zone": "time",
    "interval": "interval",
    "uuid": "uuid",
    "json": "json",
    "jsonb": "jsonb",
    "bytea": "bytea",
    "inet": "inet",
    "cidr": "cidr",
    "macaddr": "macaddr",
    "array": "array",
    "xml": "xml",
    "bit": "bit",
    "varbit": "varbit",
    "tsvector": "tsvector",
    "tsquery": "tsquery",
    # MySQL types (only those not already in PostgreSQL section)
    "mediumint": "integer",
    "int": "integer",
    "double": "float",
    "dec": "numeric",
    "tinytext": "text",
    "mediumtext": "text",
    "longtext": "text",
    "tinyblob": "blob",
    "blob": "blob",
    "mediumblob": "blob",
    "longblob": "blob",
    "binary": "binary",
    "varbinary": "binary",
    "datetime": "timestamp",
    "year": "integer",
    "enum": "enum",
    "set": "set",
    "geometry": "geometry",
    "point": "point",
    "linestring": "linestring",
    "polygon": "polygon",
}


def normalize_type(raw_type: str) -> str:
    """Canonicalize a SQL data type string to a normalized base type."""
    cleaned = raw_type.strip().lower()
    # Strip type parameters like varchar(255) -> varchar
    paren_idx = cleaned.find("(")
    if paren_idx > 0:
        cleaned = cleaned[:paren_idx]

    return _TYPE_NORMALIZATION.get(cleaned, cleaned)


# ── Diff computation ──────────────────────────────────────────────────


def _rename_similarity(old_name: str, new_name: str) -> float:
    """Simple heuristic: ratio of common prefix length to max name length."""
    if not old_name or not new_name:
        return 0.0
    common_len = 0
    for a, b in zip(old_name, new_name):
        if a == b:
            common_len += 1
        else:
            break
    return common_len / max(len(old_name), len(new_name))


_RENAME_THRESHOLD = 0.5


def compute_drift(
    before_columns: list[ColumnSchema],
    after_columns: list[ColumnSchema],
) -> DriftDelta:
    """Detect drift between two lists of ColumnSchema.

    Steps:
        1. Build name-indexed maps.
        2. Exact-name match → compare types for type change.
        3. Removed = in before but not in after (and not renamed).
        4. Added = in after but not in before (and not renamed).
        5. Rename detection: best-effort matching based on name similarity.
    """
    delta = DriftDelta()

    before_map: dict[str, ColumnSchema] = {c.name: c for c in before_columns}
    after_map: dict[str, ColumnSchema] = {c.name: c for c in after_columns}

    before_names = set(before_map.keys())
    after_names = set(after_map.keys())

    common_names = before_names & after_names

    # Check type changes for columns with same name
    for name in sorted(common_names):
        before_col = before_map[name]
        after_col = after_map[name]
        if _type_or_nullable_changed(before_col, after_col):
            delta.type_changed.append((before_col, after_col))

    # Detect added / removed / renamed
    raw_removed = before_names - after_names
    raw_added = after_names - before_names

    # Best-effort rename detection
    renamed_pairs: list[tuple[str, str]] = []
    matched_removed: set[str] = set()
    matched_added: set[str] = set()

    for old_name in sorted(raw_removed):
        best_match: str | None = None
        best_score = 0.0
        for new_name in sorted(raw_added):
            if new_name in matched_added:
                continue
            score = _rename_similarity(old_name, new_name)
            if score > best_score and score >= _RENAME_THRESHOLD:
                best_score = score
                best_match = new_name

        if best_match is not None:
            renamed_pairs.append((old_name, best_match))
            matched_removed.add(old_name)
            matched_added.add(best_match)

    for old_name, new_name in renamed_pairs:
        delta.renamed.append((before_map[old_name], after_map[new_name]))

    for name in sorted(raw_removed - matched_removed):
        delta.removed.append(before_map[name])

    for name in sorted(raw_added - matched_added):
        delta.added.append(after_map[name])

    return delta


def _type_or_nullable_changed(a: ColumnSchema, b: ColumnSchema) -> bool:
    """True if the base type, nullability, or any type detail field differs."""
    if a.data_type != b.data_type:
        return True
    if a.nullable != b.nullable:
        return True
    if a.char_max_length != b.char_max_length:
        return True
    if a.numeric_precision != b.numeric_precision:
        return True
    if a.numeric_scale != b.numeric_scale:
        return True
    if a.datetime_precision != b.datetime_precision:
        return True
    return False
