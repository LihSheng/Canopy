from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from connection.adapters.mysql_adapter import MysqlAdapter


class _Cursor:
    def __init__(self, responses: list[list[dict]]):
        self._responses = responses
        self.executed: list[tuple[str, tuple[object, ...] | None]] = []
        self._idx = 0

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        self.executed.append((query, params))

    def fetchall(self):
        response = self._responses[self._idx]
        self._idx += 1
        return response

    def fetchone(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _StreamingCursor(_Cursor):
    def __init__(self, rows: list[dict]):
        super().__init__([])
        self._rows = rows
        self._fetchmany_index = 0

    def fetchmany(self, size: int):
        start = self._fetchmany_index
        end = min(start + size, len(self._rows))
        self._fetchmany_index = end
        return self._rows[start:end]


class _Connection:
    def __init__(self, responses: list[list[dict]]):
        self.cursor_obj = _Cursor(responses)
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def close(self):
        self.closed = True


@pytest.mark.unit
def test_discover_tables_returns_table_metadata():
    conn = _Connection(
        [
            [{"TABLE_NAME": "employees", "TABLE_ROWS": 12}, {"TABLE_NAME": "payroll", "TABLE_ROWS": 8}],
            [{"COLUMN_NAME": "id", "DATA_TYPE": "bigint"}, {"COLUMN_NAME": "name", "DATA_TYPE": "varchar"}],
            [{"COLUMN_NAME": "month", "DATA_TYPE": "date"}, {"COLUMN_NAME": "amount", "DATA_TYPE": "decimal"}],
        ]
    )

    with patch("pymysql.connect", return_value=conn):
        adapter = MysqlAdapter()
        tables = asyncio.run(adapter.discover_tables({}))

    assert tables == [
        {
            "table_name": "employees",
            "row_count_estimate": 12,
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "name", "data_type": "varchar"},
            ],
        },
        {
            "table_name": "payroll",
            "row_count_estimate": 8,
            "columns": [
                {"name": "month", "data_type": "date"},
                {"name": "amount", "data_type": "decimal"},
            ],
        },
    ]
    assert conn.closed is True


@pytest.mark.unit
def test_fetch_table_streams_rows_in_batches():
    conn = _Connection(
        [
            [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Carol"},
            ]
        ]
    )
    conn.cursor_obj = _StreamingCursor(
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Carol"},
        ]
    )

    with patch("pymysql.connect", return_value=conn):
        adapter = MysqlAdapter()
        stream = asyncio.run(adapter.fetch_table({"database": "tenant_demo"}, "org_leave_type"))
        batches = asyncio.run(_collect_stream(stream))

    assert batches == [
        [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
            {"id": 3, "name": "Carol"},
        ]
    ]
    assert conn.closed is True


async def _collect_stream(stream):
    batches = []
    async for batch in stream:
        batches.append(batch)
    return batches
