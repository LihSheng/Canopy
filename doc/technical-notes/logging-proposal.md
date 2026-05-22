# Technical Note: Structured Logging Implementation

**Date:** 2026-05-22
**Scope:** Backend only
**Dependencies:** None (Python stdlib only)
**PRD:** `doc/prd/0002-logging-improvement.md`

---

## 1. Current State

### 1.1 `common/logging.py` (13 lines)

```python
def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
```

**Problem:** This function is defined but **never called** in production code. `app.py` does not import `setup_logging`. The only call site is `tests/unit/test_common.py:229`. Production runs on Python's default root logger (WARNING level, basic format, stderr), which means `LOG_LEVEL=DEBUG` in `.env` has zero effect.

### 1.2 Logger usage across codebase

| File | Lines with logger |
|------|-------------------|
| `sync/readers/pg_cdc_reader.py` | 6 calls (info/error) |
| `sync/readers/mysql_cdc_reader.py` | 5 calls (info/error) |
| **All other 300+ Python files** | **0** |

### 1.3 Stale log file inventory

```
# Project root (~18 files)
.backend-8005-v2.log       .backend-8005-v2.err.log
.backend-8005-v3.log       .backend-8005-v3.err.log
.backend-8005-v4.log       .backend-8005-v4.err.log
.backend-8005-v5.log       .backend-8005-v5.err.log
.backend-8005-v6.log       .backend-8005-v6.err.log
.backend-8005-v7.log       .backend-8005-v7.err.log
.backend-8005-20260522-095822.log   .backend-8005-20260522-095822.err.log
.backend-8005.log          .backend-8005.err.log
.backend-8001.log          .backend-8001.err.log
.frontend-3005.log         .frontend-3005.err.log
.frontend.log              .frontend.err.log
.backend.log               .backend.err.log
backend.dev.log            frontend.dev.log
backend.err.log            frontend.err.log

# apps/backend/ (2 files)
backend.8001.log           backend.8001.err.log

# apps/frontend/ (2 files)
frontend.8001.log          frontend.8001.err.log

# .codex-runlogs/ (4 files)
backend.out.log            backend.err.log
frontend.out.log           frontend.err.log
```

### 1.4 How services start

```
# Manual uvicorn — no log redirection in QUICKSTART.md
cd apps/backend && uvicorn app:app --reload --port 8005

# Ad-hoc shell redirect (how stale files got created)
uvicorn app:app --reload --port 8005 > .backend-8005-v7.log 2> .backend-8005-v7.err.log
```

There is no start script, no process manager, and no consistent log redirect pattern.

---

## 2. Proposed Architecture

```
                               Inbound Request
                                     │
                                     ▼
                         ┌─────────────────────┐
                         │ RequestIDMiddleware  │  ← sets contextvars.request_id
                         │ (X-Request-ID)       │     appends to response header
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ AccessLogMiddleware  │  ← logs method, path, status, duration_ms
                         │ (canopy.access)      │     includes request_id in log record
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ CORSMiddleware       │  ← existing
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Route handler         │  → service → repository → DB
                         │                       │    loggers in refresh/anomalies/insights
                         │                       │    use logging.getLogger(__name__)
                         └─────────────────────┘

               Log flow (per handler):
               ┌──────────────────────────────────┐
               │ 1. Console (StreamHandler)        │  human-readable, developers
               │    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
               │
               │ 2. File (RotatingFileHandler)     │  JSON, tools/grep
               │    path: apps/backend/logs/app.log
               │    maxBytes: 10_485_760 (10 MB)
               │    backupCount: 5
               │    format: JSON (see §4)
               └──────────────────────────────────┘
```

### 2.1 Context variable flow for request_id

```
Request arrives
  → RequestIDMiddleware.dispatch()
    → request_id_var.set(uuid or header value)
    → call_next(request)
      → any logger.getLogger(__name__).info("msg")
        → LogRecord created
        → RequestIDFilter.filter(record)
          → record.request_id = request_id_var.get()
        → JSONFormatter.format(record)
          → includes "request_id" in output JSON
    → response.headers["X-Request-ID"] = request_id
```

### 2.2 Middleware ordering (in app.py)

```python
# Order matters — first middleware wraps outermost
app.add_middleware(RequestIDMiddleware)      # 1st — sets context var
app.add_middleware(AccessLogMiddleware)      # 2nd — logs request, reads context var
app.add_middleware(CORSMiddleware, ...)      # 3rd — existing
```

---

## 3. Files Changed / Created

### 3.1 `apps/backend/common/logging.py` — REWRITE

**Before:** 13 lines, stdout only, never called.
**After:** ~60 lines, console + rotating JSON file.

```python
import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from common.config import settings
from common.log_context import request_id_var

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")


class RequestIDFilter(logging.Filter):
    """Injects request_id from contextvars into every log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()         # type: ignore[attr-defined]
        return True


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        rid = getattr(record, "request_id", None)
        if rid:
            payload["request_id"] = rid
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any pre-existing handlers (e.g. from uvicorn reload or test setup)
    for h in list(root.handlers):
        root.removeHandler(h)

    # --- Console handler (human-readable) ---
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    ))
    root.addHandler(console)

    # --- File handler (JSON, rotating) ---
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.addFilter(RequestIDFilter())
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)

    # Silence verbose libraries
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "passlib"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
```

**Key design decisions:**
- `RequestIDFilter` lives in `common/logging.py` because it is a logging infrastructure concern, not middleware concern. It reads the context var set by middleware.
- `JSONFormatter` uses `default=str` to handle non-serializable types (e.g. datetime in extra fields).
- `root.handlers.clear()` avoids duplicate handlers on uvicorn `--reload`.
- Third-party library loggers capped at WARNING so DEBUG mode does not flood with SQL queries.

### 3.2 `apps/backend/common/log_context.py` — NEW FILE

```python
"""Context variable for request ID propagation through log filters."""

import contextvars

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)
```

**Why separate file:** Avoids circular imports. `common/middleware.py` imports `log_context` to set the var. `common/logging.py` imports `log_context` to read the var. Neither imports the other.

### 3.3 `apps/backend/common/middleware.py` — NEW FILE

```python
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from common.log_context import request_id_var

logger = logging.getLogger("canopy.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Extracts or generates an X-Request-ID, stores in contextvars, appends to response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and duration_ms to JSON file."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
```

**Key design decisions:**
- `RequestIDMiddleware` uses `try/finally` with `contextvars.Token.reset()` — cleanest way to restore context after request.
- `AccessLogMiddleware` logs to `canopy.access` logger, NOT to `uvicorn.access` — avoids mixing with uvicorn's built-in access log.
- Duration in milliseconds with 2 decimal places for precision on fast endpoints.
- Both middlewares extend `BaseHTTPMiddleware` (Starlette) rather than `@app.middleware("http")` — more testable as plain classes.

### 3.4 `apps/backend/app.py` — MODIFY

**Before** (lines 35-102): `create_app()` has no logging setup, no custom middleware.
**After:** Three changes:

```python
# === ADD imports at top ===
from common.logging import setup_logging
from common.middleware import AccessLogMiddleware, RequestIDMiddleware

# === ADD setup_logging() as first line of create_app() ===
def create_app() -> FastAPI:
    setup_logging()
    # ... rest unchanged ...

# === ADD middleware registration after app = FastAPI(...) ===
    app = FastAPI(title="Canopy Intelligence API", version="0.1.0", lifespan=lifespan)

    # --- NEW: request ID and access logging (must come before CORS) ---
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware)

    # --- EXISTING ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3005"],
        ...
    )
```

**Also:** The module-level `app = create_app()` at line 102 will now trigger `setup_logging()` at import time. This is acceptable — it ensures logging is configured before any module uses a logger. If this becomes a problem during testing, wrap in `if __name__ == "__main__"` block later (out of scope for this change).

### 3.5 `apps/backend/refresh/orchestration/service.py` — MODIFY

Add logger and timing around stage execution. (Exact file path TBD — may be `refresh/orchestration/service.py` or `refresh/service.py` depending on actual module structure.)

```python
import logging
import time

logger = logging.getLogger(__name__)

# In the method that runs refresh stages:
async def run_refresh(self, ...):
    stages = ["sync", "normalize", "aggregate", "detect", "summarize"]
    for stage in stages:
        t0 = time.perf_counter()
        logger.info("Refresh stage starting: %s", stage)
        try:
            await self._run_stage(stage)
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info("Refresh stage complete: %s (%.0fms)", stage, elapsed)
        except Exception as e:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error("Refresh stage failed: %s (%.0fms) — %s", stage, elapsed, e)
            raise
```

### 3.6 `apps/backend/anomalies/` — MODIFY

Add logger to anomaly rule execution. Exact file depends on anomaly module structure.

```python
import logging
import time

logger = logging.getLogger(__name__)

# In anomaly detection entry point:
def detect_anomalies(self, snapshot_id: str):
    rules = [SpendSpikeRule, ClaimSurgeRule, ...]  # existing rules list
    for rule_cls in rules:
        t0 = time.perf_counter()
        rule_name = rule_cls.__name__
        logger.info("Anomaly rule starting: %s", rule_name)
        try:
            result = rule_cls().evaluate(snapshot_id)
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info("Anomaly rule complete: %s — %d anomalies found (%.0fms)",
                         rule_name, len(result), elapsed)
        except Exception as e:
            logger.error("Anomaly rule failed: %s — %s", rule_name, e)
            raise
```

### 3.7 `apps/backend/insights/service.py` — MODIFY

Add logger for AI summary generation.

```python
import logging
import time

logger = logging.getLogger(__name__)

# In summary generation entry point:
async def generate_summary(self, snapshot_id: str):
    t0 = time.perf_counter()
    logger.info("Insight generation starting for snapshot %s", snapshot_id)
    try:
        result = await self._generate(snapshot_id)
        elapsed = (time.perf_counter() - t0) * 1000
        logger.info("Insight generation complete for snapshot %s (%.0fms)", snapshot_id, elapsed)
        return result
    except Exception as e:
        logger.error("Insight generation failed for snapshot %s — %s", snapshot_id, e)
        raise
```

### 3.8 `apps/backend/logs/.gitkeep` — NEW FILE

Empty file to track `logs/` directory in git while ignoring its contents.

### 3.9 `.gitignore` (root and backend) — MODIFY

**Root `.gitignore`** — add:
```
# Log files
*.log
logs/
```

**`apps/backend/.gitignore`** — add:
```
# Log directory — keep the directory, ignore its contents
logs/*
!logs/.gitkeep
```

### 3.10 Stale log files — DELETE

Remove all files listed in §1.3 (~30 files).

### 3.11 Test files

**`apps/backend/tests/unit/test_common.py`** — extend existing `TestSetupLogging` class:

```python
class TestSetupLogging:
    # ... existing tests at line 222-240 ...

    def test_json_formatter_produces_valid_json(self):
        """JSONFormatter.format() returns parseable JSON with expected keys."""
        from common.logging import JSONFormatter
        record = logging.LogRecord("test", logging.INFO, "", 0, "hello world", (), None)
        record.request_id = "abc-123"
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "hello world"
        assert parsed["request_id"] == "abc-123"
        assert "timestamp" in parsed

    def test_json_formatter_includes_exception(self):
        """JSONFormatter includes exception info when exc_info is set."""
        from common.logging import JSONFormatter
        try:
            raise ValueError("boom")
        except ValueError:
            record = logging.LogRecord("test", logging.ERROR, "", 0, "fail", (), None)
            record.exc_info = sys.exc_info()
        formatter = JSONFormatter()
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]
```

**`apps/backend/tests/unit/test_logging_middleware.py`** — NEW FILE:

```python
"""Unit tests for RequestIDMiddleware and AccessLogMiddleware."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Scope, Receive, Send

from common.middleware import AccessLogMiddleware, RequestIDMiddleware


def make_scope(path="/api/health", headers=None):
    return {
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers or [],
    }


async def dummy_app(scope, receive, send):
    response = Response(status_code=200)
    await response(scope, receive, send)


class TestRequestIDMiddleware:
    def test_generates_uuid_when_no_header(self):
        scope = make_scope()
        middleware = RequestIDMiddleware(dummy_app)

        async def receive():
            return {"type": "http.request"}

        send_messages = []

        async def send(msg):
            send_messages.append(msg)

        # Execute
        # Note: testing BaseHTTPMiddleware requires full ASGI cycle.
        # In practice, use Starlette TestClient for integration test.
        # This unit test verifies the logic branches.
        pass  # Placeholder — see integration test approach below

    def test_header_passthrough(self):
        # Integration test via TestClient preferred
        pass

    def test_response_header_set(self):
        # Integration test via TestClient preferred
        pass


class TestAccessLogMiddleware:
    def test_logs_request_info(self):
        # Verify logger.info called with method, path, status, duration
        pass
```

**Note on middleware testing:** `BaseHTTPMiddleware` is difficult to unit-test in isolation because it requires a full ASGI request/response cycle. The recommended approach is to use FastAPI `TestClient` in an integration test or mock the ASGI app factory. The test file above shows the structure; actual implementations will use `starlette.testclient.TestClient` or `fastapi.testclient.TestClient`.

---

## 4. JSON Log Format Specification

Each line in `apps/backend/logs/app.log` is a valid JSON object (JSON Lines format).

### 4.1 Schema

```json
{
  "timestamp":       "2026-05-22T10:15:30.123456+00:00",   // ISO 8601, UTC
  "level":           "INFO" | "WARNING" | "ERROR" | "DEBUG",
  "logger":          "canopy.access" | "refresh.orchestration" | ... ,  // dotted module path
  "message":         "GET /api/health -> 200 (1.23ms)",     // human-readable summary
  "module":          "middleware",                           // __name__ module part
  "function":        "dispatch",                             // calling function
  "line":            42,                                     // source line number
  "request_id":      "550e8400-e29b-41d4-a716-446655440000", // optional, from X-Request-ID
  "exception":       "Traceback (most recent call last):\n..."  // optional, only on errors
}
```

### 4.2 Example log lines

```
# Access log
{"timestamp":"2026-05-22T10:15:30.123456+00:00","level":"INFO","logger":"canopy.access","message":"GET /api/health -> 200 (1.23ms)","module":"middleware","function":"dispatch","line":42,"request_id":"550e8400-e29b-41d4-a716-446655440000"}

# Refresh stage
{"timestamp":"2026-05-22T10:16:00.000000+00:00","level":"INFO","logger":"refresh.orchestration.service","message":"Refresh stage starting: sync","module":"service","function":"run_refresh","line":67}

# Error
{"timestamp":"2026-05-22T10:16:05.000000+00:00","level":"ERROR","logger":"refresh.orchestration.service","message":"Refresh stage failed: sync (4523ms) — ConnectionError: timeout","module":"service","function":"run_refresh","line":72,"exception":"Traceback (most recent call last):\n  File ...\nConnectionError: timeout\n"}
```

### 4.3 Quick grep patterns

```bash
# All errors
rg '"level":"ERROR"' apps/backend/logs/app.log

# Requests slower than 500ms
rg '"message":".*\(5[0-9]{2}\.' apps/backend/logs/app.log

# All lines for a specific request
rg '550e8400-e29b-41d4-a716-446655440000' apps/backend/logs/app.log

# All refresh stage timing
rg '"logger":"refresh' apps/backend/logs/app.log | rg '"level":"INFO"'
```

---

## 5. Data Flow: Request to Log

```
1. Client sends  GET /api/dashboard/summary  (no X-Request-ID header)
2. RequestIDMiddleware:
      request_id = str(uuid.uuid4())                → "a1b2c3d4-..."
      request_id_var.set("a1b2c3d4-...")           → context stored
      calls call_next(request)
3. AccessLogMiddleware:
      start = time.perf_counter()
      calls call_next(request)
4. CORSMiddleware (no-op for same-origin)
5. GET /api/dashboard/summary route handler:
      calls dashboard_service.get_summary()
        → repository.query_snapshot()
          → SQLAlchemy session.execute()
        → return summary dict
      return JSONResponse(summary)
6. Response flows back up through middleware:
      AccessLogMiddleware:
          duration_ms = (perf_counter - start) * 1000
          logger.info("GET /api/dashboard/summary -> 200 (45.21ms)")
            → LogRecord created
            → RequestIDFilter.filter()
              → record.request_id = request_id_var.get() = "a1b2c3d4-..."
            → handlers:
              a) Console (StreamHandler) → stdout, human format
              b) File (RotatingFileHandler) → JSON, includes request_id
      RequestIDMiddleware:
          response.headers["X-Request-ID"] = "a1b2c3d4-..."
          request_id_var.reset(token)
7. Client receives:
      HTTP 200
      X-Request-ID: a1b2c3d4-...
      Body: { "total_spend": ... }
```

---

## 6. Edge Cases and Tradeoffs

### 6.1 Uvicorn --reload and handler duplication

`uvicorn --reload` restarts the process on file changes. Without `root.handlers.clear()` in `setup_logging()`, each reload adds duplicate handlers. The `clear()` call prevents this.

### 6.2 Thread safety of contextvars

`contextvars.ContextVar` is thread-safe and async-safe by design. Each request (whether sync thread or async task) gets its own context. No locking needed.

### 6.3 Large traceback serialization

`JSONFormatter` uses `formatException()` which returns the full traceback as a multi-line string. This can be large for deeply nested exceptions. The 10 MB rotation limit acts as a backstop — if tracebacks are consistently too large, add truncation later.

### 6.4 Test environment isolation

`setup_logging()` is called at import time (module-level `app = create_app()`). Tests that import `app` will trigger logging configuration. The handler clear logic prevents test runs from accumulating handlers across test cases. If this becomes noisy, tests can call `logging.getLogger().handlers.clear()` in their own setup.

### 6.5 AccessLogMiddleware and streaming responses

`BaseHTTPMiddleware` reads the full response before returning. For streaming responses, this causes buffering. Canopy Intelligence v1 has no streaming endpoints — all responses are JSON. If streaming is added later, switch to `@app.middleware("http")` or a pure ASGI middleware.

### 6.6 Request ID on health checks

Health checks (`GET /api/health`) will also get request IDs logged. This is intentional — it verifies the logging pipeline is working on every health probe. If too noisy at high frequency, add path filtering later.

### 6.7 What happens when log file is unwritable

`RotatingFileHandler` raises no exception on write failure by default. If the `logs/` directory is deleted or permissions change, logs silently drop from the file handler but continue on console. This is acceptable for a development setup. For production, add `fallback` handling or a monitoring alert.

---

## 7. Verification Checklist

### 7.1 After implementation, verify:

```powershell
# 1. Log directory exists
Test-Path apps/backend/logs/app.log

# 2. Start backend
cd apps/backend && .venv\Scripts\activate && uvicorn app:app --reload --port 8005

# 3. Console shows human-readable access log after request
curl http://localhost:8005/api/health
# Console output: 2026-05-22 10:15:30,123 [INFO] canopy.access: GET /api/health -> 200 (1.23ms)

# 4. JSON file contains structured record
Get-Content apps/backend/logs/app.log | Select-Object -Last 1
# {"timestamp":"2026-05-22T...","level":"INFO","logger":"canopy.access",...}

# 5. Response includes X-Request-ID header
curl -v http://localhost:8005/api/health 2>&1 | Select-String "X-Request-ID"

# 6. Inbound X-Request-ID is passed through
curl -s http://localhost:8005/api/health -H "X-Request-ID: my-custom-id" | ...
# Log file should show "request_id":"my-custom-id"

# 7. LOG_LEVEL=DEBUG works
# Set LOG_LEVEL=DEBUG in apps/backend/.env, restart, verify debug-level log lines appear

# 8. Rotation works
# Simulate: write 10+ MB of logs, verify app.log.1 appears

# 9. Test suite passes
pytest tests/unit/test_logging_middleware.py -v
pytest tests/unit/test_common.py -v -k "test_setup_logging"

# 10. No stale log files remain in repo
git status  # should show only the new/modified files, no old *.log files
```

---

## 8. Rollback Plan

If the logging change causes issues:

1. Revert `apps/backend/common/logging.py` to original stdout-only version
2. Remove `from common.logging import setup_logging` and `setup_logging()` call from `app.py`
3. Remove `app.add_middleware(RequestIDMiddleware)` and `AccessLogMiddleware` from `app.py`
4. Delete `apps/backend/common/middleware.py` and `apps/backend/common/log_context.py`
5. Service loggers in refresh/anomalies/insights will still work — they use `logging.getLogger(__name__)` which works with Python's default root logger configuration. They just won't have structured format or request IDs.

No database changes, no migration, no frontend changes. Fully reversible.

---

## 9. Future Considerations (Not Implemented Now)

| Idea | Why not now |
|------|-------------|
| Log-level per module | Adds config complexity. One global `LOG_LEVEL` sufficient for current team size. |
| Async log handlers (queue-based) | Unnecessary for current throughput. Sync file I/O is fast enough for dev/small prod. |
| Log shipping to Loki/ELK | JSON format is ready. Integration deferred until ops tooling exists. |
| Audit log for user actions | Separate feature per ARCHITECTURE.md. Not part of structured logging infra. |
| Frontend logging | Frontend already has Next.js dev server output. Separate PRD later. |
| Structured logging in sync readers | Already have loggers. Only update if they need request_id context. |
