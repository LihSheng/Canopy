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

    def _build_conninfo(self, config: dict) -> str:
        host = config.get("host", "localhost")
        port = config.get("port", 5432)
        database = config.get("database", "")
        username = config.get("username") or config.get("user", "")
        password = config.get("password", "")
        return f"host={host} port={port} dbname={database} user={username} password={password} connect_timeout=5"

    async def _fetch_all_tables(self, config: dict) -> list[tuple[str, int]]:
        """Return list of (table_name, row_count_estimate) for all user tables."""
        conninfo = self._build_conninfo(config)
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT table_name,
                           coalesce(
                               (SELECT n_live_tup
                                FROM pg_stat_user_tables
                                WHERE relname = table_name),
                               0
                           ) AS row_estimate
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """
                )
                return [(r[0], int(r[1])) for r in await cur.fetchall()]

    async def _fetch_columns(self, config: dict, table_name: str) -> list[dict]:
        """Return column metadata for a single table."""
        conninfo = self._build_conninfo(config)
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (table_name,),
                )
                return [{"name": r[0], "data_type": r[1]} for r in await cur.fetchall()]

    async def discover_tables(self, config: dict) -> list[dict]:
        try:
            table_rows = await self._fetch_all_tables(config)
            tables: list[dict] = []
            for table_name, row_estimate in table_rows:
                columns = await self._fetch_columns(config, table_name)
                tables.append(
                    {
                        "table_name": table_name,
                        "row_count_estimate": row_estimate,
                        "columns": columns,
                    }
                )
            return tables
        except Exception:
            return []

    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        try:
            conninfo = self._build_conninfo(config)
            async with await psycopg.AsyncConnection.connect(conninfo) as conn:
                async with conn.cursor() as cur:
                    # Fetch column metadata
                    columns = await self._fetch_columns(config, table)

                    # Fetch sample rows
                    await cur.execute(
                        f'SELECT * FROM "{table}" LIMIT %s',
                        (limit,),
                    )
                    rows = await cur.fetchall()

                    ordered_rows: list[list] = []
                    for row in rows:
                        ordered_rows.append(list(row))

                    return {
                        "columns": columns,
                        "rows": ordered_rows,
                    }
        except Exception:
            return {"columns": [], "rows": []}

    async def fetch_table(
        self,
        config: dict,
        table: str,
        cursor_column: str | None = None,
        cursor_value: str | None = None,
    ) -> AsyncIterator[list[dict]]:
        conninfo = self._build_conninfo(config)

        async def generator():
            async with await psycopg.AsyncConnection.connect(conninfo) as conn:
                async with conn.cursor() as cur:
                    query = f'SELECT * FROM "{table}"'
                    params: list = []
                    if cursor_column:
                        if cursor_value is not None:
                            query += f' WHERE "{cursor_column}" > %s'
                            params.append(cursor_value)
                        query += f' ORDER BY "{cursor_column}"'

                    await cur.execute(query, tuple(params))
                    while True:
                        batch = await cur.fetchmany(500)
                        if not batch:
                            break
                        # Build dict rows manually from cursor description
                        col_names = [desc[0] for desc in cur.description] if cur.description else []
                        yield [dict(zip(col_names, row)) for row in batch]

        return generator()  # type: ignore[no-any-return]

    async def execute_query(self, config: dict, query: str, params: tuple | None = None) -> list[dict]:
        conninfo = self._build_conninfo(config)
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params or ())
                if cur.description:
                    col_names = [desc[0] for desc in cur.description]
                    rows = await cur.fetchall()
                    return [dict(zip(col_names, row)) for row in rows]
                return []
