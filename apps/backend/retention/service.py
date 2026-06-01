import uuid
from datetime import UTC, datetime

from common.errors import ValidationError
from retention.domain import (
    AUDIT_EVENT_RETENTION_CREATED,
    AUDIT_EVENT_RETENTION_UPDATED,
    PRESET_HORIZON_MAP,
    RetentionMode,
    RetentionPolicy,
    RetentionPreset,
)
from retention.repository import RetentionPolicyRepository


class RetentionPolicyService:
    def __init__(self, repo: RetentionPolicyRepository, audit_service=None):
        self._repo = repo
        self._audit = audit_service

    def get_policy(self, dataset_id: str) -> dict:
        """Return the current retention policy or a default retain-indefinitely state."""
        policy = self._repo.get_by_dataset(dataset_id)
        if policy is None:
            return self._default_policy_response(dataset_id)
        return self._policy_to_response(policy)

    def save_policy(
        self,
        dataset_id: str,
        tenant_id: str,
        actor_user_id: str,
        preset: str,
        mode: str | None = None,
        horizon_days: int | None = None,
    ) -> dict:
        """Create or update a retention policy for a dataset."""
        self._validate_policy_input(preset, mode, horizon_days)

        resolved_mode, resolved_horizon = self._resolve_policy_params(preset, mode, horizon_days)

        existing = self._repo.get_by_dataset(dataset_id)
        is_update = existing is not None

        now = datetime.now(UTC)

        if is_update:
            existing.mode = resolved_mode
            existing.horizon_days = resolved_horizon
            existing.preset = preset
            existing.is_active = True
            existing.calculated_next_action_at = self._compute_next_action(existing, resolved_mode, resolved_horizon)
            existing.updated_by = actor_user_id
            existing.updated_at = now
            policy = self._repo.save(existing)
            event_type = AUDIT_EVENT_RETENTION_UPDATED
        else:
            policy = RetentionPolicy(
                id=str(uuid.uuid4()),
                dataset_id=dataset_id,
                tenant_id=tenant_id,
                mode=resolved_mode,
                horizon_days=resolved_horizon,
                preset=preset,
                is_active=True,
                created_by=actor_user_id,
                created_at=now,
                updated_at=now,
            )
            policy.calculated_next_action_at = self._compute_next_action(policy, resolved_mode, resolved_horizon)
            policy = self._repo.save(policy)
            event_type = AUDIT_EVENT_RETENTION_CREATED

        self._record_audit(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            dataset_id=dataset_id,
            policy=policy,
        )

        return self._policy_to_response(policy)

    def _validate_policy_input(self, preset: str, mode: str | None, horizon_days: int | None) -> None:
        # Reject destructive deletion inputs in v1 (before generic validation)
        _purge_inputs = {"purge", "delete", "destroy"}
        if preset in _purge_inputs or (mode is not None and mode in _purge_inputs):
            raise ValidationError("Destructive deletion is not supported in v1")

        valid_presets = {p.value for p in RetentionPreset}
        if preset not in valid_presets:
            raise ValidationError(f"Invalid preset: {preset}")

        if preset == RetentionPreset.CUSTOM.value:
            if mode is None:
                raise ValidationError("Custom preset requires a mode")
            valid_modes = {m.value for m in RetentionMode}
            if mode not in valid_modes:
                raise ValidationError(f"Invalid mode: {mode}")
            if mode != RetentionMode.RETAIN_INDEFINITELY.value:
                if horizon_days is None:
                    raise ValidationError(f"Custom preset with mode '{mode}' requires a horizon_days value")
                if horizon_days <= 0:
                    raise ValidationError("Horizon days must be a positive integer")

    def _resolve_policy_params(self, preset: str, mode: str | None, horizon_days: int | None) -> tuple[str, int | None]:
        if preset == RetentionPreset.RETAIN_INDEFINITELY.value:
            return RetentionMode.RETAIN_INDEFINITELY.value, None

        if preset in PRESET_HORIZON_MAP:
            return RetentionMode.EXPIRE_AFTER.value, PRESET_HORIZON_MAP[preset]

        # Custom preset
        resolved_mode = mode or RetentionMode.EXPIRE_AFTER.value
        resolved_horizon = None if resolved_mode == RetentionMode.RETAIN_INDEFINITELY.value else horizon_days
        return resolved_mode, resolved_horizon

    def _compute_next_action(self, policy: RetentionPolicy, mode: str, horizon_days: int | None) -> datetime | None:
        if mode == RetentionMode.RETAIN_INDEFINITELY.value or horizon_days is None:
            return None
        base = policy.created_at
        if base is None:
            base = datetime.now(UTC)
        return base + _days_to_timedelta(horizon_days)

    def _default_policy_response(self, dataset_id: str) -> dict:
        return {
            "dataset_id": dataset_id,
            "id": None,
            "mode": RetentionMode.RETAIN_INDEFINITELY.value,
            "horizon_days": None,
            "preset": RetentionPreset.RETAIN_INDEFINITELY.value,
            "is_active": False,
            "calculated_next_action_at": None,
            "created_by": None,
            "updated_by": None,
            "created_at": None,
            "updated_at": None,
        }

    def _policy_to_response(self, policy: RetentionPolicy) -> dict:
        return {
            "dataset_id": policy.dataset_id,
            "id": policy.id,
            "mode": policy.mode,
            "horizon_days": policy.horizon_days,
            "preset": policy.preset,
            "is_active": policy.is_active,
            "calculated_next_action_at": (
                policy.calculated_next_action_at.isoformat() if policy.calculated_next_action_at else None
            ),
            "created_by": policy.created_by or None,
            "updated_by": policy.updated_by,
            "created_at": policy.created_at.isoformat() if policy.created_at else None,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
        }

    def _record_audit(
        self,
        tenant_id: str,
        actor_user_id: str,
        event_type: str,
        dataset_id: str,
        policy: RetentionPolicy,
    ) -> None:
        if self._audit is None:
            return
        self._audit.record_event(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            payload={
                "dataset_id": dataset_id,
                "policy_id": policy.id,
                "mode": policy.mode,
                "horizon_days": policy.horizon_days,
                "preset": policy.preset,
                "is_active": policy.is_active,
            },
        )


def _days_to_timedelta(days: int):
    from datetime import timedelta

    return timedelta(days=days)
