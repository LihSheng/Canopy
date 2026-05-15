# HERD Aggregator Agent Guide

Read in this order:
1. [`ARCHITECTURE.md`](./ARCHITECTURE.md)
2. [`QUICKSTART.md`](./QUICKSTART.md)
3. [`doc/codebase-map.md`](./doc/codebase-map.md)

Use this folder with these rules:
- Keep changes aligned with `ARCHITECTURE.md`.
- Do not violate the three non-negotiable rules in `ARCHITECTURE.md`.
- Keep Phase 1 boundaries intact.
- Prefer narrow, readable changes over broad rewrites.

Document roles:
- `ARCHITECTURE.md` is the source of truth for intent, boundaries, and rules.
- `doc/codebase-map.md` is a fast orientation snapshot for agents.
- If `doc/codebase-map.md` conflicts with the code, trust the code and refresh the map when part of the task.

If there is a conflict, `ARCHITECTURE.md` is the source of truth.
