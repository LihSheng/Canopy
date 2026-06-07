"""PostgreSQL Change Data Capture (CDC) reader.

Uses psycopg logical replication support to stream mutations from PostgreSQL WAL.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


class PostgresCdcReader:
    """Consumes PostgreSQL WAL logical replication stream and writes mutation events."""

    def __init__(self, config: dict, dataset_id: str, table_name: str):
        self.config = config
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.running = False

    async def start_streaming(self, storage_path: Path, on_event: Callable[[dict], Any] | None = None) -> None:
        """Start logical replication stream.

        Writes streamed events to the dataset storage directory.
        """
        self.running = True

        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        database = self.config.get("database", "")
        username = self.config.get("username") or self.config.get("user", "")
        password = self.config.get("password", "")
        slot_name = self.config.get("cdc_parameters", {}).get("replication_slot_name", f"canopy_slot_{database}")
        publication_name = f"canopy_pub_{self.table_name}"

        # Connect in replication mode
        conninfo = f"host={host} port={port} dbname={database} user={username} password={password} connect_timeout=5"
        async with await psycopg.AsyncConnection.connect(conninfo, autocommit=True) as check_conn:
            async with check_conn.cursor() as cur:
                # Create publication if not exists
                await cur.execute(f"SELECT 1 FROM pg_publication WHERE pubname = '{publication_name}';")
                if not await cur.fetchone():
                    await cur.execute(f"CREATE PUBLICATION {publication_name} FOR TABLE {self.table_name};")

                # Create logical replication slot if not exists
                await cur.execute(f"SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_name}';")
                if not await cur.fetchone():
                    await cur.execute(f"SELECT pg_create_logical_replication_slot('{slot_name}', 'test_decoding');")

        logger.info(f"Connecting to replication stream with slot: {slot_name}")
        async with await psycopg.AsyncConnection.connect(conninfo, replication="database") as conn:
            # Use test_decoding or pgoutput plugin
            async with conn.cursor() as cur:
                await cur.execute(f"START_REPLICATION SLOT {slot_name} LOGICAL 0/0;")

                while self.running:
                    try:
                        # Await logical replication message
                        msg = await conn.receive()  # type: ignore[attr-defined]
                        if msg is None:
                            continue

                        # Parse pg logical replication test_decoding output format
                        # e.g., table public.users: INSERT: id[integer]:1 name[character varying]:'Alice'
                        payload_str = (
                            msg.payload.decode("utf-8") if isinstance(msg.payload, bytes) else str(msg.payload)
                        )

                        event = {
                            "timestamp": datetime.now(UTC).isoformat(),
                            "lsn": str(msg.wal_start),
                            "payload": payload_str,
                        }

                        # Append mutation event to JSONL file
                        with open(storage_path, "a", encoding="utf-8") as f:
                            f.write(json.dumps(event) + "\n")

                        if on_event:
                            on_event(event)

                        # Send feedback to keep replication slot alive
                        conn.send_feedback(write_lsn=msg.wal_start)  # type: ignore[attr-defined]

                    except asyncio.CancelledError:
                        break
                    except Exception as inner_err:
                        logger.error(f"Error reading replication message: {inner_err}")
                        await asyncio.sleep(1)

    def stop(self) -> None:
        """Stop the logical replication streaming reader."""
        self.running = False
