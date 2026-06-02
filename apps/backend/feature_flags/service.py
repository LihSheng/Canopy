from feature_flags.repository import FeatureFlagRepository


class FeatureFlagService:
    """Service for managing global feature flags.

    Wraps repository with seeding and read/write operations.
    """

    def __init__(self, repo: FeatureFlagRepository):
        self._repo = repo

    def get_all(self) -> list[dict]:
        flags = self._repo.get_all()
        return [
            {
                "flag_key": f.flag_key,
                "description": f.description,
                "enabled": f.enabled,
            }
            for f in flags
        ]

    def get_enabled_map(self) -> dict[str, bool]:
        return self._repo.get_enabled()

    def set_flag(self, flag_key: str, enabled: bool) -> dict | None:
        flag = self._repo.set_enabled(flag_key, enabled)
        if not flag:
            return None
        return {
            "flag_key": flag.flag_key,
            "description": flag.description,
            "enabled": flag.enabled,
        }

    def seed_defaults(self) -> None:
        """Seed default feature flags if they do not exist."""
        defaults = [
            {
                "flag_key": "entity_canvas_enabled",
                "description": (
                    "Enable the Entity Designer Graph Canvas as the primary editor path for Entity config."
                ),
                "enabled": True,
            },
        ]
        self._repo.seed_defaults(defaults)
