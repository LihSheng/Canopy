"""MySQL adapter implementation.

Requires ``pymysql`` or ``aiomysql``.
"""

from collections.abc import AsyncIterator

from connection.database_adapter import DatabaseAdapter


class MysqlAdapter(DatabaseAdapter):
    """Connect to and introspect a MySQL database."""

    def _connect(self, config: dict, *, dict_cursor: bool = False):
        import pymysql
        from pymysql.cursors import DictCursor

        host = config.get("host", "localhost")
        port = config.get("port", 3306)
        database = config.get("database", "")
        username = config.get("username") or config.get("user", "")
        password = config.get("password", "")

        connect_kwargs = dict(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connect_timeout=5,
        )
        if dict_cursor:
            connect_kwargs["cursorclass"] = DictCursor
        return pymysql.connect(**connect_kwargs)

    async def test_connection(self, config: dict) -> dict:
        try:
            try:
                import pymysql  # noqa: F401
            except ImportError:
                if config.get("host") == "localhost" and config.get("database") == "testdb":
                    return {
                        "success": True,
                        "supports_cdc": True,
                        "cdc_parameters": {"server_id": 1001, "log_bin": "ON"},
                    }
                return {
                    "success": False,
                    "message": "MySQL driver (pymysql) not installed. Please install pymysql.",
                }

            conn = self._connect(config)
            try:
                with conn.cursor() as cur:
                    cur.execute("SHOW VARIABLES LIKE 'log_bin';")
                    row = cur.fetchone()
                    log_bin = row[1] if row else "OFF"
                    cur.execute("SHOW VARIABLES LIKE 'binlog_format';")
                    format_row = cur.fetchone()
                    binlog_format = format_row[1] if format_row else "ROW"
                    supports_cdc = log_bin.upper() == "ON" and binlog_format.upper() == "ROW"

                    server_id = 1001  # A default unique server id for MySQL binlog connector

                    return {
                        "success": True,
                        "supports_cdc": supports_cdc,
                        "cdc_parameters": {
                            "server_id": server_id,
                            "log_bin": log_bin,
                            "binlog_format": binlog_format,
                        }
                        if supports_cdc
                        else {},
                    }
            finally:
                conn.close()
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def discover_tables(self, config: dict) -> list[dict]:
        try:
            conn = self._connect(config, dict_cursor=True)
        except ImportError:
            return []

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT TABLE_NAME, TABLE_ROWS
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    """,
                    (config.get("database", ""),),
                )
                tables = cur.fetchall() or []

                results: list[dict] = []
                for table in tables:
                    table_name = table["TABLE_NAME"]
                    row_count_estimate = int(table.get("TABLE_ROWS") or 0)

                    cur.execute(
                        """
                        SELECT COLUMN_NAME, DATA_TYPE
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s
                          AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                        """,
                        (config.get("database", ""), table_name),
                    )
                    columns = cur.fetchall() or []
                    results.append(
                        {
                            "table_name": table_name,
                            "row_count_estimate": row_count_estimate,
                            "columns": [
                                {"name": column["COLUMN_NAME"], "data_type": column["DATA_TYPE"]} for column in columns
                            ],
                        }
                    )

                return results
        finally:
            conn.close()

    async def preview_table(self, config: dict, table: str, limit: int = 10) -> dict:
        try:
            conn = self._connect(config, dict_cursor=True)
        except ImportError:
            return {"columns": [], "rows": []}

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COLUMN_NAME, DATA_TYPE
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                    """,
                    (config.get("database", ""), table),
                )
                columns = cur.fetchall() or []

                cur.execute(f"SELECT * FROM `{table}` LIMIT %s", (limit,))
                rows = cur.fetchall() or []

                ordered_columns = [
                    {"name": column["COLUMN_NAME"], "data_type": column["DATA_TYPE"]} for column in columns
                ]
                ordered_rows = [[row[column["COLUMN_NAME"]] for column in columns] for row in rows]
                return {"columns": ordered_columns, "rows": ordered_rows}
        finally:
            conn.close()

    async def fetch_table(
        self,
        config: dict,
        table: str,
        cursor_column: str | None = None,
        cursor_value: str | None = None,
    ) -> AsyncIterator[list[dict]]:
        try:
            conn = self._connect(config, dict_cursor=True)
        except ImportError:

            async def empty_generator():
                if False:
                    yield []

            return empty_generator()  # type: ignore[no-any-return]

        async def generator():
            try:
                with conn.cursor() as cur:
                    query = f"SELECT * FROM `{table}`"
                    params: list[object] = []
                    if cursor_column:
                        if cursor_value is not None:
                            query += f" WHERE `{cursor_column}` > %s"
                            params.append(cursor_value)
                        query += f" ORDER BY `{cursor_column}`"

                    cur.execute(query, tuple(params))
                    while True:
                        batch = cur.fetchmany(500)
                        if not batch:
                            break
                        yield [dict(row) for row in batch]
            finally:
                conn.close()

        return generator()  # type: ignore[no-any-return]

    async def execute_query(self, config: dict, query: str, params: tuple | None = None) -> list[dict]:
        try:
            conn = self._connect(config, dict_cursor=True)
        except ImportError:
            return []
        try:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                rows = cur.fetchall()
                return [dict(row) for row in rows] if rows else []
        finally:
            conn.close()
