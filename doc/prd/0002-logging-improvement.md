# PRD: Structured Logging Infrastructure

**Status:** Ready for implementation
**Date:** 2026-05-22
**Scope:** Backend only

---

## Problem Statement

As a developer debugging the Canopy Intelligence backend, I cannot trace a request through the stack. There is no correlation ID, no structured log format, and no centralized log directory. The `setup_logging()` function exists in `common/logging.py` but is never called in production — logging falls back to Python defaults (WARNING level, plain text, stderr only). Only 2 of 300+ Python files use a logger. All file output relies on ad-hoc shell redirects (`uvicorn ... > file 2> file`), producing ~30 stale log files scattered across the project with no naming convention and no rotation or cleanup. When a 500 error occurs, I must hunt through multiple `.err.log` files in different directories with no way to correlate log lines to a specific request.

ARCHITECTURE.md section "Observability" (lines 503–506) requires recording sync duration, failure reasons, refresh timing, anomaly timing, and AI summary errors. None of this is currently instrumented.

## Solution

A lightweight, zero-dependency structured logging system that:

1. Wires `setup_logging()` into app startup so `LOG_LEVEL` in `.env` actually works
2. Writes human-readable logs to console and structured JSON logs to a rotating file
3. Injects a correlation ID (`X-Request-ID`) into every request and attaches it to log records
4. Logs every request (method, path, status, duration) via FastAPI middleware
5. Adds logger instrumentation to the three modules ARCHITECTURE.md explicitly names for observability: refresh orchestration, anomaly detection, and insight generation
6. Cleans up ~30 stale log files and establishes a single canonical log directory

No new dependencies. Uses only Python stdlib `logging`, `RotatingFileHandler`, `contextvars`, and `json.dumps`.

## User Stories

1. As a developer, I want `LOG_LEVEL=DEBUG` in `.env` to actually take effect, so I can increase verbosity without code changes.
2. As a developer, I want every log line tagged with a request ID, so I can trace a single request from middleware through services to the database.
3. As a developer, I want structured JSON log output, so I can grep, filter, and aggregate logs with standard tools.
4. As a developer, I want human-readable logs on stdout during development, so I can read them without parsing JSON manually.
5. As a developer, I want log files to auto-rotate and auto-delete old backups, so my disk does not fill up over time.
6. As a developer, I want all log files in one canonical directory, so I never waste time searching multiple directories for the right `.err.log` file.
7. As a developer, I want every HTTP request logged with method, path, status, and duration, so I can identify slow or failing endpoints at a glance.
8. As a developer, I want refresh sync stage timing logged (start, end, duration, failure), so I can debug slow or failed sync jobs.
9. As a developer, I want anomaly rule execution timing logged, so I can identify which rules are expensive.
10. As a developer, I want AI insight generation errors logged, so I can debug why summaries are missing or wrong.
11. As a developer, I want stale log files deleted from the repo, so `git status` stays clean and I do not accidentally commit old logs.
12. As a future operator, I want JSON log format compatible with Loki and ELK, so I can plug into a log aggregation stack without reformatting.

## Implementation Decisions

### Log output targets
- **Console:** human-readable format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- **File:** JSON via `RotatingFileHandler` to `apps/backend/logs/app.log`

### Log directory
- Canonical location: `apps/backend/logs/`
- Tracked with `.gitkeep`; all `*.log` files git-ignored

### Rotation policy
- 10 MB per file, 5 backups kept (~60 MB max total)
- Standard Python `RotatingFileHandler`

### Correlation ID
- Header: `X-Request-ID` (industry standard, proxies pass it through)
- Generated as UUID4 if not present on inbound request
- Injected into response headers for client-side tracing
- Attached to log records via `contextvars` + custom `logging.Filter`

### Request logging
- `AccessLogMiddleware` — logs method, path, status code, duration_ms to JSON file
- Uvicorn built-in access log stays on console (plain text); does NOT go to JSON file
- No duplicate lines — two streams, no overlap

### Module instrumentation (minimal scope)
Only modules explicitly named by ARCHITECTURE.md "Observability":

| Module | What to log |
|--------|-------------|
| Refresh orchestration | Stage start/end, duration per stage, failure reason |
| Anomaly detection | Rule execution start/end, rule name, execution time |
| Insight generation | Generation start/end, error details on failure |
| Sync readers (already done) | Already have loggers — no change |

### Library noise suppression
- `sqlalchemy.engine` capped at WARNING (avoids SQL query spam even at DEBUG level)
- `uvicorn.access` capped at WARNING in our handlers (its own console output stays)

### No new dependencies
All implementation uses Python 3.11+ stdlib: `logging`, `logging.handlers.RotatingFileHandler`, `json`, `contextvars`, `uuid`.

### No monitoring integration (yet)
JSON format is designed to be compatible with Loki (JSON log driver) and ELK (JSON lines). No integration code ships now — pure format compatibility.

## Testing Decisions

### What makes a good test
- Test external behavior: what logs are produced, what headers are set, what JSON shape is emitted
- Do not test internal handler wiring — verify the observable output
- Mock file I/O where needed to avoid touching disk

### Modules to test
1. **`setup_logging()`** — verify handlers are configured, log level applied, JSON formatter produces valid JSON
2. **`RequestIDMiddleware`** — verify: generates UUID when no header, reuses header when present, sets response header
3. **`AccessLogMiddleware`** — verify: logs method, path, status, duration_ms; includes request_id in context
4. **`JSONFormatter`** — verify: valid JSON output, all expected keys present, exception serialized correctly

### Prior art in codebase
- `apps/backend/tests/unit/test_common.py` — already tests `setup_logging()` at lines 220–240. These tests will be extended, not replaced.

### Test files
- `apps/backend/tests/unit/test_common.py` — extend existing `TestSetupLogging`
- `apps/backend/tests/unit/test_logging_middleware.py` — new file for middleware tests

## Out of Scope

- Frontend logging (Next.js already has console output; revisit later)
- Log aggregation integration (Loki, ELK, Datadog)
- Log-level-per-module configuration (all modules share `LOG_LEVEL`)
- Structured logging in `sync/readers/` beyond what already exists
- Performance metrics or tracing (separate from logging)
- Alerting rules or log-based monitoring
- Log shipping or forwarding
- Audit log for user actions (separate feature)

## Further Notes

### Stale log file cleanup
Approximately 30 log files will be deleted as part of implementation:
- Project root: all `.backend-*.log`, `.backend-*.err.log`, `.frontend-*.log`, `.frontend-*.err.log`, `backend.*.log`, `frontend.*.log`, `.backend.log`, `.backend.err.log`, `.frontend.log`, `.frontend.err.log`
- `apps/backend/`: `backend.8001.log`, `backend.8001.err.log`
- `apps/frontend/`: `frontend.8001.log`, `frontend.8001.err.log`
- `.codex-runlogs/`: `backend.out.log`, `backend.err.log`, `frontend.out.log`, `frontend.err.log`

### Files modified/created
See technical note for exact file list and diff shapes.

### Design decision record
No ADR required — this is an incremental infrastructure improvement within existing `common/` module boundaries, consistent with ARCHITECTURE.md cross-cutting concerns.
