from contextvars import ContextVar
from dataclasses import dataclass


@dataclass
class TenantContext:
    tenant_id: str
    tenant_role: str
    membership_status: str
    is_impersonated: bool = False
    database_target_ref: str | None = None
    active_token_id: str | None = None


_current_tenant_ctx: ContextVar[TenantContext | None] = ContextVar(
    "current_tenant_ctx", default=None
)


def set_current_tenant_context(ctx: TenantContext) -> None:
    _current_tenant_ctx.set(ctx)


def get_current_tenant_context() -> TenantContext | None:
    return _current_tenant_ctx.get()


def reset_tenant_context() -> None:
    _current_tenant_ctx.set(None)
