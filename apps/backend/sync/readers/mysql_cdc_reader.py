"""MySQL Change Data Capture (CDC) reader.

Uses mysql-replication (BinLogStreamReader) to stream row-based mutations from MySQL binary logs.
"""

import asyncio
import json
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MysqlCdcReader:
    """Consumes MySQL binary logs row events and writes mutation events."""

    def __init__(self, config: dict, dataset_id: str, table_name: str):
        self.config = config
        self.dataset_id = dataset_id
        self.table_name = table_name
        self.running = False

    async def start_streaming(self, storage_path: Path, on_event: Callable[[dict], Any] | None = None) -> None:
        """Start MySQL binlog streaming.

        Writes streamed events to the dataset storage directory.
        """
        self.running = True

        # Ensure directory exists
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        host = self.config.get("host", "localhost")
        port = self.config.get("port", 3306)
        database = self.config.get("database", "")
        username = self.config.get("username") or self.config.get("user", "")
        password = self.config.get("password", "")
        server_id = self.config.get("cdc_parameters", {}).get("server_id", 1001)

        # Dynamic import of mysql-replication to prevent import errors if not installed
        from mysqlreplication import BinLogStreamReader
        from mysqlreplication.row_event import DeleteRowsEvent, UpdateRowsEvent, WriteRowsEvent

        mysql_settings = {"host": host, "port": port, "user": username, "passwd": password}

        logger.info(f"Connecting to MySQL binlog stream at {host}:{port} for db {database}")

        # Start binlog streaming reader
        # only_events filters to row events only:
        # WriteRowsEvent (Insert), UpdateRowsEvent (Update), DeleteRowsEvent (Delete)
        stream = BinLogStreamReader(
            connection_settings=mysql_settings,
            server_id=server_id,
            only_schemas=[database],
            only_tables=[self.table_name],
            only_events=[WriteRowsEvent, UpdateRowsEvent, DeleteRowsEvent],
            blocking=True,
        )

        try:
            while self.running:
                # Let's read binlog events in a non-blocking asyncio-friendly fashion
                # Since stream.fetchone() is blocking, we run it in executor
                loop = asyncio.get_running_loop()
                binlogevent = await loop.run_in_executor(None, stream.fetchone)

                if binlogevent is None:
                    continue

                for row in binlogevent.rows:
                    op = "INSERT"
                    data = row["values"]

                    if isinstance(binlogevent, UpdateRowsEvent):
                        op = "UPDATE"
                        data = row["after_values"]
                    elif isinstance(binlogevent, DeleteRowsEvent):
                        op = "DELETE"
                        data = row["values"]

                    event = {
                        "timestamp": datetime.now(UTC).isoformat(),
                        "op": op,
                        "table": self.table_name,
                        "data": data,
                        "binlog_file": stream.log_file,
                        "binlog_pos": stream.log_pos,
                    }

                    with open(storage_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(event) + "\n")

                    if on_event:
                        on_event(event)

        finally:
            stream.close()

    def stop(self) -> None:
        """Stop the binlog streaming reader."""
        self.running = False
