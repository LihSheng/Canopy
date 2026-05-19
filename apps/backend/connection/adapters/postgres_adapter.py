"""PostgreSQL adapter implementation.

Requires ``asyncpg``.
"""

from collections.abc import AsyncIterator

from connection.database_adapter import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """Connect to and introspect a PostgreSQL database."""

    async def test_connection(self, config: dict) -> dict:
        raise NotImplementedError("PostgresAdapter.test_connection not yet implemented")

    async def discover_tables(self, config: dict) -> list[dict]:
        raise NotImplementedError("PostgresAdapter.discover_tables not yet implemented")

    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        raise NotImplementedError("PostgresAdapter.preview_table not yet implemented")

    async def fetch_table(
        self,
        config: dict,
        table: str,
        cursor_column: str | None = None,
        cursor_value: str | None = None,
    ) -> AsyncIterator[list[dict]]:
        raise NotImplementedError("PostgresAdapter.fetch_table not yet implemented")
