from unittest.mock import MagicMock

import pytest

from common.errors import ValidationError
from retention.domain import (
    AUDIT_EVENT_RETENTION_CREATED,
    AUDIT_EVENT_RETENTION_UPDATED,
    RetentionMode,
    RetentionPolicy,
    RetentionPreset,
)
from retention.service import RetentionPolicyService


def _make_policy(**overrides) -> RetentionPolicy:
    defaults = {
        "id": "rp-001",
        "dataset_id": "ds-001",
        "tenant_id": "t-001",
        "mode": RetentionMode.RETAIN_INDEFINITELY.value,
        "horizon_days": None,
        "preset": RetentionPreset.RETAIN_INDEFINITELY.value,
        "is_active": True,
        "calculated_next_action_at": None,
        "created_by": "user-001",
    }
    defaults.update(overrides)
    return RetentionPolicy(**defaults)


class TestGetPolicy:
    def test_returns_default_when_no_policy_exists(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        service = RetentionPolicyService(repo)

        result = service.get_policy("ds-001")

        assert result["dataset_id"] == "ds-001"
        assert result["id"] is None
        assert result["mode"] == RetentionMode.RETAIN_INDEFINITELY.value
        assert result["is_active"] is False

    def test_returns_existing_policy(self):
        policy = _make_policy(
            mode=RetentionMode.EXPIRE_AFTER.value,
            horizon_days=90,
            preset=RetentionPreset.DAYS_90.value,
        )
        repo = MagicMock()
        repo.get_by_dataset.return_value = policy
        service = RetentionPolicyService(repo)

        result = service.get_policy("ds-001")

        assert result["dataset_id"] == "ds-001"
        assert result["id"] == "rp-001"
        assert result["mode"] == RetentionMode.EXPIRE_AFTER.value
        assert result["horizon_days"] == 90
        assert result["preset"] == RetentionPreset.DAYS_90.value
        assert result["is_active"] is True


class TestSavePolicyPresets:
    def test_save_retain_indefinitely_preset(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        audit = MagicMock()
        service = RetentionPolicyService(repo, audit_service=audit)

        result = service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.RETAIN_INDEFINITELY.value,
        )

        assert result["mode"] == RetentionMode.RETAIN_INDEFINITELY.value
        assert result["horizon_days"] is None
        assert result["preset"] == RetentionPreset.RETAIN_INDEFINITELY.value

    @pytest.mark.parametrize(
        "preset,expected_days",
        [
            ("30_days", 30),
            ("90_days", 90),
            ("1_year", 365),
            ("7_years", 2555),
        ],
    )
    def test_save_finite_presets(self, preset, expected_days):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        audit = MagicMock()
        service = RetentionPolicyService(repo, audit_service=audit)

        result = service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=preset,
        )

        assert result["mode"] == RetentionMode.EXPIRE_AFTER.value
        assert result["horizon_days"] == expected_days
        assert result["preset"] == preset

    def test_save_custom_preset_with_expire(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        audit = MagicMock()
        service = RetentionPolicyService(repo, audit_service=audit)

        result = service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset="custom",
            mode=RetentionMode.EXPIRE_AFTER.value,
            horizon_days=180,
        )

        assert result["mode"] == RetentionMode.EXPIRE_AFTER.value
        assert result["horizon_days"] == 180


class TestSavePolicyValidation:
    def test_rejects_invalid_preset(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="Invalid preset"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="nonexistent",
            )

    def test_custom_preset_requires_mode(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="Custom preset requires a mode"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="custom",
                mode=None,
                horizon_days=30,
            )

    def test_custom_preset_rejects_invalid_mode(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="Invalid mode"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="custom",
                mode="invalid_mode",
                horizon_days=30,
            )

    def test_custom_preset_requires_positive_horizon(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="positive integer"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="custom",
                mode=RetentionMode.EXPIRE_AFTER.value,
                horizon_days=0,
            )

    def test_custom_preset_requires_horizon_for_finite_mode(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="requires a horizon_days"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="custom",
                mode=RetentionMode.EXPIRE_AFTER.value,
                horizon_days=None,
            )

    def test_rejects_destructive_deletion_purge_mode(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="Destructive deletion"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="custom",
                mode="purge",
                horizon_days=30,
            )

    def test_rejects_destructive_deletion_purge_preset(self):
        repo = MagicMock()
        service = RetentionPolicyService(repo)

        with pytest.raises(ValidationError, match="Destructive deletion"):
            service.save_policy(
                dataset_id="ds-001",
                tenant_id="t-001",
                actor_user_id="user-001",
                preset="purge",
            )


class TestSavePolicyAudit:
    def test_creates_audit_event_on_new_policy(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p  # return the actual saved policy
        audit = MagicMock()
        service = RetentionPolicyService(repo, audit_service=audit)

        service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.DAYS_90.value,
        )

        audit.record_event.assert_called_once()
        call_kwargs = audit.record_event.call_args.kwargs
        assert call_kwargs["event_type"] == AUDIT_EVENT_RETENTION_CREATED
        assert call_kwargs["tenant_id"] == "t-001"
        assert call_kwargs["actor_user_id"] == "user-001"
        assert call_kwargs["payload"]["dataset_id"] == "ds-001"
        assert call_kwargs["payload"]["preset"] == RetentionPreset.DAYS_90.value

    def test_creates_audit_event_on_update(self):
        existing = _make_policy()
        repo = MagicMock()
        repo.get_by_dataset.return_value = existing
        repo.save.return_value = existing
        audit = MagicMock()
        service = RetentionPolicyService(repo, audit_service=audit)

        service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.DAYS_30.value,
        )

        audit.record_event.assert_called_once()
        call_kwargs = audit.record_event.call_args.kwargs
        assert call_kwargs["event_type"] == AUDIT_EVENT_RETENTION_UPDATED

    def test_no_audit_when_audit_service_not_provided(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        service = RetentionPolicyService(repo)

        # Should not raise
        service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.DAYS_90.value,
        )


class TestCalculatedNextAction:
    def test_retain_indefinitely_has_no_next_action(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        service = RetentionPolicyService(repo)

        result = service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.RETAIN_INDEFINITELY.value,
        )

        assert result["calculated_next_action_at"] is None

    def test_finite_policy_has_calculated_date(self):
        repo = MagicMock()
        repo.get_by_dataset.return_value = None
        repo.save.side_effect = lambda p: p
        service = RetentionPolicyService(repo)

        result = service.save_policy(
            dataset_id="ds-001",
            tenant_id="t-001",
            actor_user_id="user-001",
            preset=RetentionPreset.DAYS_30.value,
        )

        assert result["calculated_next_action_at"] is not None


class TestPresetHorizonMap:
    def test_all_presets_have_correct_values(self):
        from retention.domain import PRESET_HORIZON_MAP

        assert PRESET_HORIZON_MAP["30_days"] == 30
        assert PRESET_HORIZON_MAP["90_days"] == 90
        assert PRESET_HORIZON_MAP["1_year"] == 365
        assert PRESET_HORIZON_MAP["7_years"] == 2555
