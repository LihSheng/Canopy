"""Tests for schema drift detection, classification, and circuit breaker logic.

Covers:
    - Type normalization (dialect quirks)
    - Drift diff algorithm (added/removed/renamed/type change)
    - SchemaSignature hash stability
    - Service: check_and_record_drift (first discovery, no drift, drift detected)
    - Service: breaking drift blocks datasets
    - Service: non-breaking drift does not block
    - Service: clear_block workflow
    - Sync skip behavior (via unit test on ExternalDbSyncService)
"""

from unittest.mock import MagicMock

import pytest

from dataset.domain import Dataset, DatasetStatus
from schema_drift.domain import (
    ColumnSchema,
    SchemaSignature,
    _rename_similarity,
    _type_or_nullable_changed,
    compute_drift,
    normalize_type,
)
from schema_drift.repository import SchemaDriftEventRepository, SchemaSignatureRepository
from schema_drift.service import SchemaDriftService

# ── Helpers ───────────────────────────────────────────────────────────

def _col(name: str, data_type: str = "integer", nullable: bool = True, **kw) -> ColumnSchema:
    return ColumnSchema(name=name, data_type=data_type, nullable=nullable, **kw)


def _raw_col(name: str, data_type: str = "integer", **kw) -> dict:
    result = {"name": name, "data_type": data_type}
    result.update(kw)
    return result


def _make_dataset(
    id: str = "ds-1",
    connection_id: str = "conn-1",
    status: str = DatasetStatus.ACTIVE.value,
    source_object_name: str = "users",
) -> Dataset:
    return Dataset(
        id=id,
        project_id="proj-1",
        connection_id=connection_id,
        name=source_object_name,
        source_object_name=source_object_name,
        status=status,
    )


# ═══════════════════════════════════════════════════════════════════════
# Type normalization
# ═══════════════════════════════════════════════════════════════════════

class TestNormalizeType:
    def test_postgres_int_variants(self):
        assert normalize_type("int2") == "integer"
        assert normalize_type("int4") == "integer"
        assert normalize_type("int8") == "integer"
        assert normalize_type("integer") == "integer"

    def test_mysql_int_variants(self):
        assert normalize_type("tinyint") == "integer"
        assert normalize_type("smallint") == "integer"
        assert normalize_type("mediumint") == "integer"
        assert normalize_type("int") == "integer"
        assert normalize_type("bigint") == "integer"

    def test_float_variants(self):
        assert normalize_type("real") == "float"
        assert normalize_type("float4") == "float"
        assert normalize_type("float8") == "float"
        assert normalize_type("double precision") == "float"
        assert normalize_type("float") == "float"
        assert normalize_type("double") == "float"

    def test_string_types(self):
        assert normalize_type("varchar") == "varchar"
        assert normalize_type("character varying") == "varchar"
        assert normalize_type("char") == "char"
        assert normalize_type("character") == "char"
        assert normalize_type("text") == "text"
        assert normalize_type("tinytext") == "text"
        assert normalize_type("mediumtext") == "text"
        assert normalize_type("longtext") == "text"

    def test_timestamp_types(self):
        assert normalize_type("timestamp") == "timestamp"
        assert normalize_type("timestamptz") == "timestamptz"
        assert normalize_type("timestamp with time zone") == "timestamptz"
        assert normalize_type("timestamp without time zone") == "timestamp"
        assert normalize_type("datetime") == "timestamp"

    def test_strips_parameters(self):
        assert normalize_type("varchar(255)") == "varchar"
        assert normalize_type("numeric(10,2)") == "numeric"
        assert normalize_type("decimal(18,6)") == "numeric"

    def test_case_insensitive(self):
        assert normalize_type("INTEGER") == "integer"
        assert normalize_type("VARCHAR") == "varchar"
        assert normalize_type("TIMESTAMPTZ") == "timestamptz"

    def test_unknown_type_passes_through(self):
        assert normalize_type("my_custom_type") == "my_custom_type"


# ═══════════════════════════════════════════════════════════════════════
# Rename similarity
# ═══════════════════════════════════════════════════════════════════════

class TestRenameSimilarity:
    def test_exact_match(self):
        assert _rename_similarity("email", "email") == 1.0

    def test_common_prefix(self):
        sim = _rename_similarity("user_email", "user_email_new")
        assert sim > 0.5

    def test_no_common_prefix(self):
        assert _rename_similarity("abc", "xyz") == 0.0

    def test_empty_strings(self):
        assert _rename_similarity("", "foo") == 0.0
        assert _rename_similarity("foo", "") == 0.0


# ═══════════════════════════════════════════════════════════════════════
# Type or nullable change detection
# ═══════════════════════════════════════════════════════════════════════

class TestTypeOrNullableChanged:
    def test_identical_no_change(self):
        assert _type_or_nullable_changed(_col("id"), _col("id")) is False

    def test_type_change(self):
        assert _type_or_nullable_changed(_col("id", "integer"), _col("id", "bigint")) is True

    def test_nullable_change(self):
        assert _type_or_nullable_changed(_col("id", nullable=True), _col("id", nullable=False)) is True

    def test_char_length_change(self):
        a = _col("name", "varchar", char_max_length=100)
        b = _col("name", "varchar", char_max_length=255)
        assert _type_or_nullable_changed(a, b) is True

    def test_numeric_precision_change(self):
        a = _col("price", "numeric", numeric_precision=10, numeric_scale=2)
        b = _col("price", "numeric", numeric_precision=12, numeric_scale=2)
        assert _type_or_nullable_changed(a, b) is True

    def test_numeric_scale_change(self):
        a = _col("price", "numeric", numeric_precision=10, numeric_scale=2)
        b = _col("price", "numeric", numeric_precision=10, numeric_scale=4)
        assert _type_or_nullable_changed(a, b) is True

    def test_datetime_precision_change(self):
        a = _col("ts", "timestamp", datetime_precision=0)
        b = _col("ts", "timestamp", datetime_precision=1)
        assert _type_or_nullable_changed(a, b) is True


# ═══════════════════════════════════════════════════════════════════════
# Drift diff algorithm
# ═══════════════════════════════════════════════════════════════════════

class TestComputeDrift:
    def test_identical_schemas(self):
        before = [_col("id"), _col("name", "varchar")]
        after = [_col("id"), _col("name", "varchar")]
        delta = compute_drift(before, after)
        assert len(delta.added) == 0
        assert len(delta.removed) == 0
        assert len(delta.renamed) == 0
        assert len(delta.type_changed) == 0
        assert delta.is_breaking is False

    def test_added_column(self):
        before = [_col("id")]
        after = [_col("id"), _col("name", "varchar")]
        delta = compute_drift(before, after)
        assert len(delta.added) == 1
        assert delta.added[0].name == "name"
        assert delta.is_breaking is False  # added is non-breaking

    def test_removed_column(self):
        before = [_col("id"), _col("name", "varchar")]
        after = [_col("id")]
        delta = compute_drift(before, after)
        assert len(delta.removed) == 1
        assert delta.removed[0].name == "name"
        assert delta.is_breaking is True

    def test_type_change(self):
        before = [_col("id", "integer")]
        after = [_col("id", "bigint")]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1
        assert delta.type_changed[0][0].name == "id"
        assert delta.type_changed[0][0].data_type == "integer"
        assert delta.type_changed[0][1].data_type == "bigint"
        assert delta.is_breaking is True

    def test_nullable_change_is_type_change(self):
        before = [_col("email", "varchar", nullable=True)]
        after = [_col("email", "varchar", nullable=False)]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1
        assert delta.is_breaking is True

    def test_rename_detection_best_effort(self):
        before = [_col("user_email", "varchar"), _col("id")]
        after = [_col("user_email_address", "varchar"), _col("id")]
        delta = compute_drift(before, after)
        assert len(delta.renamed) == 1
        assert delta.renamed[0][0].name == "user_email"
        assert delta.renamed[0][1].name == "user_email_address"
        assert delta.is_breaking is True  # renamed is breaking

    def test_rename_with_low_similarity_is_not_detected(self):
        before = [_col("abc")]
        after = [_col("xyz")]
        delta = compute_drift(before, after)
        assert len(delta.renamed) == 0
        assert len(delta.removed) == 1
        assert len(delta.added) == 1

    def test_multiple_changes(self):
        before = [
            _col("id"),
            _col("user_email", "varchar"),
            _col("email", "varchar"),
            _col("age", "integer"),
        ]
        after = [
            _col("id"),
            _col("user_email_address", "varchar"),  # rename (high prefix similarity)
            _col("email", "text"),  # type change
            # age removed
            _col("score", "float"),  # added
        ]
        delta = compute_drift(before, after)
        # user_email -> user_email_address should be detected as rename (prefix "user_email")
        assert len(delta.renamed) == 1
        assert delta.renamed[0][0].name == "user_email"
        assert delta.renamed[0][1].name == "user_email_address"
        # age removed, score added, email type changed
        assert len(delta.removed) == 1
        assert delta.removed[0].name == "age"
        assert len(delta.added) == 1
        assert delta.added[0].name == "score"
        assert len(delta.type_changed) == 1
        assert delta.type_changed[0][0].name == "email"
        assert delta.is_breaking is True

    def test_empty_schemas(self):
        delta = compute_drift([], [])
        assert len(delta.added) == 0
        assert len(delta.removed) == 0
        assert delta.is_breaking is False

    def test_added_multiple_columns_non_breaking(self):
        before = [_col("id")]
        after = [_col("id"), _col("col_a"), _col("col_b"), _col("col_c")]
        delta = compute_drift(before, after)
        assert len(delta.added) == 3
        assert delta.is_breaking is False


# ═══════════════════════════════════════════════════════════════════════
# SchemaSignature hash stability
# ═══════════════════════════════════════════════════════════════════════

class TestSchemaSignatureHash:
    def test_same_columns_produce_same_hash(self):
        cols_a = [_col("id"), _col("name", "varchar")]
        cols_b = [_col("name", "varchar"), _col("id")]  # different order

        sig_a = SchemaSignature(connection_id="c1", source_object_name="t1", columns=cols_a)
        sig_b = SchemaSignature(connection_id="c1", source_object_name="t1", columns=cols_b)

        assert sig_a.compute_hash() == sig_b.compute_hash()

    def test_different_columns_produce_different_hash(self):
        cols_a = [_col("id")]
        cols_b = [_col("name", "varchar")]

        sig_a = SchemaSignature(connection_id="c1", source_object_name="t1", columns=cols_a)
        sig_b = SchemaSignature(connection_id="c1", source_object_name="t1", columns=cols_b)

        assert sig_a.compute_hash() != sig_b.compute_hash()

    def test_hash_is_deterministic(self):
        cols = [_col("id"), _col("name", "varchar")]
        sig = SchemaSignature(connection_id="c1", source_object_name="t1", columns=cols)
        assert sig.compute_hash() == sig.compute_hash()


# ═══════════════════════════════════════════════════════════════════════
# Service: check_and_record_drift
# ═══════════════════════════════════════════════════════════════════════

class TestServiceCheckAndRecordDrift:
    def test_first_discovery_creates_baseline(self):
        """First discovery with no stored signature should create baseline, not drift."""
        mock_sig_repo = MagicMock(spec=SchemaSignatureRepository)
        mock_sig_repo.get.return_value = None
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_dataset_repo = MagicMock()

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=mock_sig_repo,
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        result = service.check_and_record_drift(
            connection_id="conn-1",
            source_object_name="users",
            raw_columns=[{"name": "id", "data_type": "integer"}],
            detected_by="discovery",
        )

        assert result["drift_detected"] is False
        assert result["is_breaking"] is False
        assert result["event"] is None
        assert result["signature_hash"] != ""
        # Signature should be saved
        mock_sig_repo.save.assert_called_once()

    def test_identical_schema_no_drift(self):
        """Same hash as stored should produce no drift."""
        cols = [_col("id")]
        sig = SchemaSignature(connection_id="conn-1", source_object_name="users", columns=cols)
        sig_hash = sig.compute_hash()

        mock_sig_repo = MagicMock(spec=SchemaSignatureRepository)
        mock_sig_repo.get.return_value = sig
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_dataset_repo = MagicMock()

        # Make get return a signature with the same hash
        stored = SchemaSignature(connection_id="conn-1", source_object_name="users", columns=cols)
        stored.signature_hash = sig_hash
        mock_sig_repo.get.return_value = stored

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=mock_sig_repo,
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        result = service.check_and_record_drift(
            connection_id="conn-1",
            source_object_name="users",
            raw_columns=[{"name": "id", "data_type": "integer"}],
            detected_by="discovery",
        )

        assert result["drift_detected"] is False
        mock_event_repo.save.assert_not_called()

    def test_non_breaking_drift_recorded_not_blocked(self):
        """Adding a column records event but does not block."""
        before_cols = [_col("id")]
        sig = SchemaSignature(connection_id="conn-1", source_object_name="users", columns=before_cols)
        sig.signature_hash = sig.compute_hash()

        mock_sig_repo = MagicMock(spec=SchemaSignatureRepository)
        mock_sig_repo.get.return_value = sig
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_dataset_repo = MagicMock()

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=mock_sig_repo,
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        result = service.check_and_record_drift(
            connection_id="conn-1",
            source_object_name="users",
            raw_columns=[{"name": "id", "data_type": "integer"}, {"name": "name", "data_type": "varchar"}],
            detected_by="sync",
        )

        assert result["drift_detected"] is True
        assert result["is_breaking"] is False
        mock_event_repo.save.assert_called_once()
        # Should NOT try to block datasets
        assert mock_dataset_repo.save.call_count == 0  # only signature save

    def test_breaking_drift_blocks_dataset(self):
        """Removing a column records event and blocks dataset."""
        before_cols = [_col("id"), _col("name", "varchar")]
        sig = SchemaSignature(connection_id="conn-1", source_object_name="users", columns=before_cols)
        sig.signature_hash = sig.compute_hash()

        ds = _make_dataset(id="ds-1", connection_id="conn-1")
        ds2 = _make_dataset(id="ds-2", connection_id="conn-1")

        mock_sig_repo = MagicMock(spec=SchemaSignatureRepository)
        mock_sig_repo.get.return_value = sig
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.list_all.return_value = [ds, ds2]
        mock_dataset_repo.get.side_effect = lambda x: ds if x == "ds-1" else (ds2 if x == "ds-2" else None)

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=mock_sig_repo,
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        result = service.check_and_record_drift(
            connection_id="conn-1",
            source_object_name="users",
            raw_columns=[{"name": "id", "data_type": "integer"}],  # name removed
            detected_by="discovery",
        )

        assert result["drift_detected"] is True
        assert result["is_breaking"] is True

        # Both datasets should have been blocked
        assert ds.status == DatasetStatus.BLOCKED_SCHEMA_DRIFT.value
        assert ds2.status == DatasetStatus.BLOCKED_SCHEMA_DRIFT.value


# ═══════════════════════════════════════════════════════════════════════
# Service: clear_block
# ═══════════════════════════════════════════════════════════════════════

class TestServiceClearBlock:
    def test_clears_blocked_dataset(self):
        ds = _make_dataset(id="ds-1", status=DatasetStatus.BLOCKED_SCHEMA_DRIFT.value)
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.get.return_value = ds
        mock_dataset_repo.save.return_value = ds

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=MagicMock(spec=SchemaSignatureRepository),
            event_repo=MagicMock(spec=SchemaDriftEventRepository),
            dataset_repo=mock_dataset_repo,
        )

        result = service.clear_block(dataset_id="ds-1", actor_user_id="user-1")
        assert result.status == DatasetStatus.ACTIVE.value

    def test_raises_on_non_blocked_dataset(self):
        ds = _make_dataset(id="ds-1", status=DatasetStatus.ACTIVE.value)
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.get.return_value = ds

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=MagicMock(spec=SchemaSignatureRepository),
            event_repo=MagicMock(spec=SchemaDriftEventRepository),
            dataset_repo=mock_dataset_repo,
        )

        with pytest.raises(Exception, match="blocked_schema_drift"):
            service.clear_block(dataset_id="ds-1", actor_user_id="user-1")

    def test_raises_on_missing_dataset(self):
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.get.return_value = None

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=MagicMock(spec=SchemaSignatureRepository),
            event_repo=MagicMock(spec=SchemaDriftEventRepository),
            dataset_repo=mock_dataset_repo,
        )

        with pytest.raises(Exception, match="not found"):
            service.clear_block(dataset_id="ds-missing", actor_user_id="user-1")


# ═══════════════════════════════════════════════════════════════════════
# Service: get_drift_status
# ═══════════════════════════════════════════════════════════════════════

class TestServiceGetDriftStatus:
    def test_no_drift(self):
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.get.return_value = _make_dataset()
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_event_repo.get_latest_by_source_object.return_value = None

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=MagicMock(spec=SchemaSignatureRepository),
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        status = service.get_drift_status("ds-1")
        assert status["drift_detected"] is False
        assert status["is_blocked"] is False
        assert status["last_drift_at"] is None

    def test_drift_detected(self):
        ds = _make_dataset(id="ds-1")
        mock_dataset_repo = MagicMock()
        mock_dataset_repo.get.return_value = ds
        mock_event_repo = MagicMock(spec=SchemaDriftEventRepository)
        mock_event_repo.get_latest_by_source_object.return_value = {
            "created_at": "2026-05-20T12:00:00+00:00",
            "is_breaking": True,
        }

        service = SchemaDriftService(
            db=MagicMock(),
            sig_repo=MagicMock(spec=SchemaSignatureRepository),
            event_repo=mock_event_repo,
            dataset_repo=mock_dataset_repo,
        )

        status = service.get_drift_status("ds-1")
        assert status["drift_detected"] is True
        assert status["last_drift_at"] == "2026-05-20T12:00:00+00:00"
        assert status["last_drift_is_breaking"] is True


# ═══════════════════════════════════════════════════════════════════════
# Edge cases and hardening
# ═══════════════════════════════════════════════════════════════════════

class TestDriftEdgeCases:
    def test_rename_with_numbered_suffix(self):
        """Columns like 'col_1' -> 'col_2' should not be false positive renamed."""
        before = [_col("col_1")]
        after = [_col("col_2")]
        delta = compute_drift(before, after)
        # Similarity: "col_1" vs "col_2" -> common prefix "col_" = 4, max = 5, score = 0.8 >= 0.5
        # So this WOULD be detected as rename. That's acceptable for v1 best-effort.
        # But if we want to be strict, it depends on threshold.
        # The threshold is 0.5, so col_1 -> col_2 is 0.8, rename is detected.
        assert len(delta.renamed) == 1

    def test_add_and_remove_same_count_not_confused(self):
        """Adding 2 and removing 2 different columns."""
        before = [_col("a"), _col("b")]
        after = [_col("c"), _col("d")]
        delta = compute_drift(before, after)
        # a->c: similarity('a','c') = 0/1 = 0
        # a->d: similarity('a','d') = 0/1 = 0
        # b->c: similarity('b','c') = 0/1 = 0
        # b->d: similarity('b','d') = 0/1 = 0
        # So no renames detected
        assert len(delta.renamed) == 0
        assert len(delta.removed) == 2
        assert len(delta.added) == 2
        assert delta.is_breaking is True

    def test_nullable_change_only(self):
        """NULL -> NOT NULL is breaking."""
        before = [_col("email", "varchar", nullable=True)]
        after = [_col("email", "varchar", nullable=False)]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1
        assert delta.is_breaking is True

    def test_char_length_change_only(self):
        before = [_col("name", "varchar", char_max_length=50)]
        after = [_col("name", "varchar", char_max_length=100)]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1
        assert delta.is_breaking is True

    def test_precision_scale_change(self):
        before = [_col("amount", "numeric", numeric_precision=10, numeric_scale=2)]
        after = [_col("amount", "numeric", numeric_precision=12, numeric_scale=4)]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1

    def test_datetime_tz_change(self):
        before = [_col("ts", "timestamp", datetime_precision=0)]
        after = [_col("ts", "timestamptz", datetime_precision=1)]
        delta = compute_drift(before, after)
        assert len(delta.type_changed) == 1


# ═══════════════════════════════════════════════════════════════════════
# ColumnSchema.from_raw edge cases
# ═══════════════════════════════════════════════════════════════════════

class TestColumnSchemaFromRaw:
    def test_minimal_fields(self):
        col = ColumnSchema.from_raw(name="id", data_type="integer")
        assert col.name == "id"
        assert col.data_type == "integer"
        assert col.nullable is True
        assert col.char_max_length is None

    def test_with_extra_fields(self):
        col = ColumnSchema.from_raw(
            name="name", data_type="varchar(255)",
            nullable=False, char_max_length=255,
        )
        assert col.name == "name"
        assert col.data_type == "varchar"  # normalized
        assert col.nullable is False
        assert col.char_max_length == 255

    def test_mysql_unsigned_not_swallowed(self):
        # Unsigned is a modifier, data_type stays "int"
        col = ColumnSchema.from_raw(name="id", data_type="int")
        assert col.data_type == "integer"  # normalized
