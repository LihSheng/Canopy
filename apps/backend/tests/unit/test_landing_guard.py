"""Unit tests for the landing-zone preservation guard."""

import pytest

from common.errors import IngestionTransformNotAllowedError
from ingestion.landing_guard import (
    blocked_ingestion_keys,
    reject_transform_keys,
)


class TestBlockedIngestionKeys:
    def test_known_keys_are_blocked(self):
        blocked = blocked_ingestion_keys()
        assert "transformations" in blocked
        assert "cleaning_steps" in blocked
        assert "column_mappings" in blocked
        assert "rename_columns" in blocked
        assert "drop_columns" in blocked
        assert "cast_rules" in blocked
        assert "filters" in blocked
        assert "masking_rules" in blocked
        assert "normalization_rules" in blocked

    def test_returns_frozenset(self):
        blocked = blocked_ingestion_keys()
        assert isinstance(blocked, frozenset)


class TestRejectTransformKeys:
    def test_clean_payload_passes(self):
        reject_transform_keys({"name": "test", "project_id": "p1"})

    def test_empty_payload_passes(self):
        reject_transform_keys({})

    def test_non_dict_payload_passes(self):
        reject_transform_keys("not a dict")  # type: ignore[arg-type]
        reject_transform_keys(None)  # type: ignore[arg-type]

    def test_blocks_single_transform_key_top_level(self):
        with pytest.raises(IngestionTransformNotAllowedError) as exc_info:
            reject_transform_keys({"name": "test", "cleaning_steps": []})
        assert exc_info.value.code == "INGESTION_TRANSFORM_NOT_ALLOWED"
        assert exc_info.value.status_code == 422
        assert "not allowed at landing stage" in exc_info.value.message
        assert exc_info.value.blocked_keys == ["cleaning_steps"]

    def test_blocks_multiple_transform_keys(self):
        with pytest.raises(IngestionTransformNotAllowedError) as exc_info:
            reject_transform_keys(
                {
                    "name": "test",
                    "cleaning_steps": [],
                    "column_mappings": {},
                    "filters": "x > 0",
                }
            )
        assert exc_info.value.code == "INGESTION_TRANSFORM_NOT_ALLOWED"
        assert exc_info.value.status_code == 422
        blocked = exc_info.value.blocked_keys
        assert "cleaning_steps" in blocked
        assert "column_mappings" in blocked
        assert "filters" in blocked
        assert len(blocked) == 3

    def test_blocks_all_nine_known_keys(self):
        payload = {
            "transformations": [],
            "cleaning_steps": [],
            "column_mappings": {},
            "rename_columns": {},
            "drop_columns": [],
            "cast_rules": [],
            "filters": [],
            "masking_rules": [],
            "normalization_rules": [],
        }
        with pytest.raises(IngestionTransformNotAllowedError) as exc_info:
            reject_transform_keys(payload)
        assert len(exc_info.value.blocked_keys) == 9

    # --- nested-key detection (config_json smuggling) ---

    def test_blocks_transform_key_inside_nested_dict(self):
        with pytest.raises(IngestionTransformNotAllowedError) as exc_info:
            reject_transform_keys(
                {
                    "project_id": "p1",
                    "config_json": {
                        "host": "localhost",
                        "cleaning_steps": ["trim"],
                    },
                }
            )
        assert "config_json.cleaning_steps" in exc_info.value.blocked_keys

    def test_blocks_multiple_nested_keys_across_sections(self):
        with pytest.raises(IngestionTransformNotAllowedError) as exc_info:
            reject_transform_keys(
                {
                    "project_id": "p1",
                    "config_json": {
                        "host": "localhost",
                        "transformations": ["uppercase"],
                    },
                    "extra_settings": {
                        "filters": ["x > 1"],
                    },
                }
            )
        blocked = exc_info.value.blocked_keys
        assert "config_json.transformations" in blocked
        assert "extra_settings.filters" in blocked

    def test_nested_payload_with_only_clean_keys_passes(self):
        reject_transform_keys(
            {
                "config_json": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                }
            }
        )

    def test_shallow_only_checks_one_level_deep(self):
        """Keys nested two levels deep should NOT be detected (by design)."""
        # This passes because the guard only checks one level deep.
        reject_transform_keys(
            {
                "config_json": {
                    "nested": {
                        "cleaning_steps": ["should not be found"],
                    }
                }
            }
        )

    def test_non_dict_values_are_skipped(self):
        payload: dict = {
            "name": "test",
            "config_json": "not a dict but a string",
        }
        reject_transform_keys(payload)

    # --- edge cases ---

    def test_transform_key_with_none_value_is_blocked(self):
        with pytest.raises(IngestionTransformNotAllowedError):
            reject_transform_keys({"name": "test", "cleaning_steps": None})

    def test_transform_key_with_empty_list_is_blocked(self):
        with pytest.raises(IngestionTransformNotAllowedError):
            reject_transform_keys({"name": "test", "cleaning_steps": []})
