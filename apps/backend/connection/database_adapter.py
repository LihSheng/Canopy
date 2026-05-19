"""Abstract adapter for external database connections.

Each adapter implementation handles a specific database dialect and
encapsulates all source-specific SQL and driver logic.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class DatabaseAdapter(ABC):
    """Interface for connecting to and introspecting an external database."""

    @abstractmethod
    async def test_connection(self, config: dict) -> dict:
        """Verify the connection credentials are valid.

        Returns ``{"success": True}`` or ``{"success": False, "message": str}``.
        """

    @abstractmethod
    async def discover_tables(self, config: dict) -> list[dict]:
        """Return metadata for all user-accessible tables.

        Each entry::

            {
                "table_name": str,
                "row_count_estimate": int,
                "columns": [{"name": str, "data_type": str}],
            }
        """

    @abstractmethod
    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        """Return sample rows and column schema for a table.

        Returns ``{"columns": [{"name": str, "data_type": str}], "rows": [list]}]``.
        """

    @abstractmethod
    async def fetch_table(
        self,
        config: dict,
        table: str,
        cursor_column: str | None = None,
        cursor_value: str | None = None,
    ) -> AsyncIterator[list[dict]]:
        """Stream all rows from a table in batches for batch sync.

        Each yielded batch is a list of dicts keyed by column name.
        When ``cursor_column`` and ``cursor_value`` are provided, only
        rows where ``cursor_column > cursor_value`` are returned
        (incremental cursor mode).

        This is the primary method for the sync engine. Unlike
        ``preview_table`` it is NOT limited to a small sample and
        MUST support streaming batches to avoid memory exhaustion.
        """


def get_adapter(source_type: str) -> DatabaseAdapter:
    """Return the adapter for a given source type key.

    Raises ``ValueError`` if the source type is not supported.
    """
    from connection.adapters.postgres_adapter import PostgresAdapter
    from connection.adapters.mysql_adapter import MysqlAdapter

    registry: dict[str, DatabaseAdapter] = {
        "postgresql": PostgresAdapter(),
        "mysql": MysqlAdapter(),
    }
    if source_type not in registry:
        raise ValueError(f"Unsupported source type: {source_type}")
    return registry[source_type]
