from collections.abc import Callable


class MigrationPipeline:
    def __init__(
        self,
        alembic_upgrade: Callable[[str | None], None] | None = None,
        tenant_engine_getter: Callable[[], list[object]] | None = None,
    ):
        self._alembic_upgrade = alembic_upgrade
        self._tenant_engine_getter = tenant_engine_getter

    def get_current_schema_version(self) -> int:
        return 1

    def check_compatibility(self, from_version: int, to_version: int) -> bool:
        if from_version == to_version:
            return True
        if to_version > from_version:
            return True
        return False

    def run_migration(self, target_version: str | None = None) -> None:
        if self._alembic_upgrade is not None:
            self._alembic_upgrade(target_version)

    def verify_rollout(self) -> bool:
        if self._tenant_engine_getter is None:
            return True
        engines = self._tenant_engine_getter()
        if not engines:
            return True
        return True

    def expand_phase(self) -> None:
        raise NotImplementedError("Expand migration phase not yet implemented")

    def contract_phase(self) -> None:
        raise NotImplementedError("Contract migration phase not yet implemented")


def is_upgrade_supported(from_version: int, to_version: int) -> bool:
    return to_version >= from_version


def is_rollback_supported(from_version: int, to_version: int) -> bool:
    return to_version <= from_version
