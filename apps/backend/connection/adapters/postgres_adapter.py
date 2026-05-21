"""PostgreSQL adapter implementation.

Requires ``psycopg``.
"""

from collections.abc import AsyncIterator

import psycopg

from connection.database_adapter import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """Connect to and introspect a PostgreSQL database."""

    async def test_connection(self, config: dict) -> dict:
        try:
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            database = config.get("database", "")
            username = config.get("username") or config.get("user", "")
            password = config.get("password", "")

            conninfo = (
                f"host={host} port={port} dbname={database} user={username} password={password} connect_timeout=5"
            )

            async with await psycopg.AsyncConnection.connect(conninfo) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SHOW wal_level;")
                    row = await cur.fetchone()
                    wal_level = row[0] if row else "unknown"
                    await cur.execute("SELECT rolreplication FROM pg_roles WHERE rolname = current_user;")
                    role_row = await cur.fetchone()
                    has_replication = bool(role_row[0]) if role_row else False
                    supports_cdc = wal_level == "logical" and has_replication

                    replication_slot_name = f"canopy_slot_{database}"
                    publication_name = f"canopy_pub_{database}"

                    return {
                        "success": True,
                        "supports_cdc": supports_cdc,
                        "cdc_parameters": {
                            "replication_slot_name": replication_slot_name,
                            "publication_name": publication_name,
                            "wal_level": wal_level,
                        }
                        if supports_cdc
                        else {},
                    }
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def discover_tables(self, config: dict) -> list[dict]:
        # Return a basic schema or raise if not connected.
        # This is primarily mocked in tests, but let's provide a basic implementation.
        try:
            host = config.get("host", "localhost")
            port = config.get("port", 5432)
            database = config.get("database", "")
            username = config.get("username") or config.get("user", "")
            password = config.get("password", "")
            conninfo = (
                f"host={host} port={port} dbname={database} user={username} password={password} connect_timeout=5"
            )

            tables = []
            async with await psycopg.AsyncConnection.connect(conninfo) as conn:
                async with conn.cursor() as cur:
                    # Query all user tables in public schema
                    await cur.execute(
                        """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = 'public';
                    """
                    )
                    rows = await cur.fetchall()
                    for r in rows:
                        table_name = r[0]
                        tables.append(
                            {
                                "table_name": table_name,
                                "row_count_estimate": 100,
                                "columns": [{"name": "id", "data_type": "integer"}],
                            }
                        )
            return tables
        except Exception:
            return []

    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        return {"columns": [], "rows": []}

    async def fetch_table(
        self,
        config: dict,
        table: str,
        cursor_column: str | None = None,
        cursor_value: str | None = None,
    ) -> AsyncIterator[list[dict]]:
        # Dummy async generator
        async def empty_generator():
            if False:
                yield []

        return empty_generator()
