from collections.abc import Callable

_listeners: list[Callable] = []


def register_listener(callback: Callable) -> None:
    _listeners.append(callback)


def _notify(event_type: str, tenant_id: str, **kwargs) -> None:
    for listener in _listeners:
        listener(event_type, tenant_id, **kwargs)


def after_tenant_provisioned(tenant_id: str) -> None:
    _notify("provisioned", tenant_id)


def after_tenant_suspended(tenant_id: str) -> None:
    _notify("suspended", tenant_id)


def after_tenant_restored(tenant_id: str) -> None:
    _notify("restored", tenant_id)


def after_config_changed(tenant_id: str, key: str) -> None:
    _notify("config_changed", tenant_id, key=key)


def after_database_rotation(tenant_id: str, old_ref: str, new_ref: str) -> None:
    _notify("database_rotation", tenant_id, old_ref=old_ref, new_ref=new_ref)


def after_schema_rollout() -> None:
    _notify("schema_rollout", "")
