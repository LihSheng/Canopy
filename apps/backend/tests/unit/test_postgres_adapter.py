"""Tests for PostgresAdapter."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from connection.adapters.postgres_adapter import PostgresAdapter


@pytest.mark.asyncio
async def test_fetch_table_error_propagates_on_stream_failure():
    """When the data stream breaks mid-way, the error propagates to the caller."""
    mock_cursor = AsyncMock()
    mock_cursor.description = [("id",), ("name",)]
    # First fetchmany call succeeds, second raises ConnectionError
    mock_cursor.fetchmany = AsyncMock(side_effect=[[(1, "Alice")], ConnectionError("connection lost")])
    mock_cursor.execute = AsyncMock()
    mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
    mock_cursor.__aexit__ = AsyncMock(return_value=None)

    mock_conn = AsyncMock()
    mock_conn.cursor = MagicMock(return_value=mock_cursor)
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)

    with patch("psycopg.AsyncConnection.connect", AsyncMock(return_value=mock_conn)):
        adapter = PostgresAdapter()
        generator = await adapter.fetch_table({"host": "localhost"}, "users")

        collected = []
        with pytest.raises(ConnectionError, match="connection lost"):
            async for batch in generator:
                collected.extend(batch)

        # Partial data before the failure is preserved
        assert len(collected) == 1
        assert collected[0]["id"] == 1
