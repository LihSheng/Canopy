"""MySQL adapter implementation.

Requires ``aiomysql`` or ``mysql-connector-python``.
"""

from connection.database_adapter import DatabaseAdapter


class MysqlAdapter(DatabaseAdapter):
    """Connect to and introspect a MySQL database."""

    async def test_connection(self, config: dict) -> dict:
        raise NotImplementedError("MysqlAdapter.test_connection not yet implemented")

    async def discover_tables(self, config: dict) -> list[dict]:
        raise NotImplementedError("MysqlAdapter.discover_tables not yet implemented")

    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        raise NotImplementedError("MysqlAdapter.preview_table not yet implemented")
