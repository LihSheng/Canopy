# Canopy Intelligence Enhancement Roadmap

## Version

**Status:** Draft — Phase 7-13 planning
**Date:** 2026-06-09
**Source:** Derived from [Palantir-Canopy Comparison](palantir-canopy-comparison.md)

---

## Table of Contents

1. [Vision Statement](#vision-statement)
2. [Design Principles](#design-principles)
3. [Phase 7: Universal Connector Framework](#phase-7-universal-connector-framework)
4. [Phase 8: Dynamic Ontology Builder](#phase-8-dynamic-ontology-builder)
5. [Phase 9: Multi-Modal Analytics Engine](#phase-9-multi-modal-analytics-engine)
6. [Phase 10: Application Builder & Widget System](#phase-10-application-builder--widget-system)
7. [Phase 11: AI Platform](#phase-11-ai-platform)
8. [Phase 12: Developer Platform & API](#phase-12-developer-platform--api)
9. [Phase 13: Automation & Observability](#phase-13-automation--observability)
10. [Timeline](#timeline)
11. [Resource Summary](#resource-summary)
12. [Decision Points](#decision-points)
13. [Success Metrics](#success-metrics)
14. [Risk Register](#risk-register)

---

## Vision Statement

Canopy Intelligence evolves from an executive HR spend intelligence platform into a **multi-source data operating system for organizational analytics**.

The evolution preserves Canopy's core strengths — deterministic analytics and snapshot-scoped consistency — while adding the capabilities needed to connect to any source, model data dynamically, execute approved operational actions, build analytics without code, and augment every workflow with AI.

By the end of Phase 13, Canopy will be:

- **Source-agnostic:** Connect to any database, API, or file format through a unified connector framework
- **Ontology-driven:** Users define their own object types, properties, and relationships through a visual interface
- **Analytics-rich:** Multi-dimensional aggregations, time series, statistical functions, and composable dashboards
- **AI-augmented:** Conversational analytics, semantic search, and AI-assisted dashboard generation
- **Developer-friendly:** REST APIs, SDKs, webhooks, and MCP integration for external builders
- **Production-grade:** Automated alerting, workflow lineage, data health monitoring, and audit logging

---

## Design Principles

The following principles carry forward from `ARCHITECTURE.md` and are extended for the platform phase:

1. **Explicit actions only.** The system may write to approved connected systems and Canopy-owned tables through explicit, policy-checked workflows. No hidden side effects.
2. **Deterministic analytics decide. The LLM narrates.** All metrics, aggregations, and anomaly detections are computed by code first. AI provides explanation and assistance, never invention.
3. **Snapshot-scoped consistency.** Dashboard, export, and AI summaries must all use the same data snapshot. No real-time updates that bypass the refresh pipeline.
4. **Tenant-aware at every seam.** Even when single-tenant, all code assumes a tenant context. No global mutable state.
5. **Source isolation.** Source-specific schema knowledge stays inside connector and mapper boundaries. Downstream modules consume normalized objects.
6. **Domain names over phase labels.** No `v7_`, `v8_` prefixes in runtime code. Use `connector`, `ontology`, `analytics`, `widget` as names.
7. **Composability over monolithic dashboards.** The application surface becomes a canvas of configurable widgets, not a set of hardcoded pages.
8. **AI is a layer, not a shortcut.** AI capabilities are built on top of deterministic analytics and structured ontology data, not as replacements for them.

---

## Phase 7: Universal Connector Framework

**Goal:** Move from 3 hardcoded source types to an extensible connector framework with read and action capabilities.

**Why now:** Without universal connectors, Canopy cannot ingest the breadth of data needed for a dynamic ontology or generic analytics, or execute approved operations against connected systems. This is the foundation for everything that follows.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 7.1 | **Connector Base Class** | Abstract `Connector` with `connect()`, `discover_schema()`, `read_batch()`, `read_stream()`, `execute_action()`, `health_check()`, `close()` | Medium | 2w |
| 7.2 | **JDBC Connector** | Generic JDBC adapter covering PostgreSQL, MySQL, SQL Server, Oracle, BigQuery, Snowflake, Redshift, with supported write actions where the target allows them | Low | 3w |
| 7.3 | **REST API Connector** | Configurable REST connector with pagination, auth (OAuth2, API key, Basic), JSON→tabular normalization, and action execution for supported endpoints | Medium | 4w |
| 7.4 | **File Connector Expansion** | Extend static file to CSV, JSON, Parquet, Avro with schema inference | Low | 3w |
| 7.5 | **Connector Wizard UI** | Frontend wizard: add connection → test → preview schema → configure sync | Medium | 3w |
| 7.6 | **Sync Policy Engine** | Per-connector schedule config (cron, interval, manual), incremental sync support, action policy config, sync history | Low | 3w |
| 7.7 | **Connection Health Monitoring** | Per-connector health status, latency metrics, failure tracking, retry logic | Low | 2w |
| 7.8 | **Connector Registry** | Database table storing connector types, configurations, credentials (encrypted), action scopes, and tenant scoping | Low | 2w |

**Resource estimate:** 2-3 engineers, 22 engineering weeks

**Verification:** A user can add a new PostgreSQL connection via the UI, configure a sync schedule, see the schema preview, have the data appear in the staging zone within the scheduled interval, and run an approved connector action where the target supports it.

**Dependencies:** None — builds on v6 connection work.

### Phase 7 Iteration Plan

Phase 7 should ship as a sequence of narrow slices, each one ending in a usable checkpoint.

| Milestone | Scope | Deliverables | Exit Criteria |
|---|---|---|---|
| 7.0 | **Connector contract and policy model** | Action schema, permission scope model, idempotency key rule, audit event schema, connector registry shape | One stable contract covers all later action types |
| 7.1 | **Read path foundation** | JDBC read support, REST read support, file read support, schema discovery, health check, registry persistence | A user can connect a source, preview schema, and run a scheduled read sync |
| 7.2 | **Create / Update actions** | `execute_action()` for create and update, request validation, result handling, audit logging, UI action trigger surface | A user can perform an approved create or update action end-to-end |
| 7.3 | **Approval workflow** | Pending-approval state, approver assignment, approval UI, notification hook, timeout handling | An action can pause for approval, resume, or be rejected with full audit trail |
| 7.4 | **Delete actions** | Delete policy rules, soft-delete or undo strategy, stronger permissions, confirmation UX | A delete action runs only under explicit elevated policy |
| 7.5 | **Webhook-triggered actions** | Webhook ingress, signature verification, dedupe, delivery retries, event-to-action mapping | An external event can trigger a controlled action safely |

Recommended order:
- 7.0 first, because every later action depends on it
- 7.1 next, because the platform still needs the core connector value
- 7.2 next, because create/update gives the first action capability without the highest-risk paths
- 7.3 after that, because approvals add governance without changing the action model
- 7.4 before 7.5, because delete is riskier but simpler than external event intake
- 7.5 last, because webhook delivery and dedupe add the most operational complexity

---

## Phase 8: Dynamic Ontology Builder

**Goal:** Replace the 6 hardcoded domain types with a user-definable ontology system.

**Why now:** Once data can come from any source (Phase 7), users need a way to define what business objects exist in that data. A dynamic ontology is the bridge between raw data and meaningful analytics.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 8.1 | **Ontology Type Schema** | Database schema for `object_types`, `properties`, `property_types`, `object_type_groups`, with tenant scoping | Medium | 2w |
| 8.2 | **Object Type Editor UI** | Interface to create/edit object types: name, properties (name, type, required, primary key, title), description | High | 4w |
| 8.3 | **Dynamic Backing Datasource Binding** | Per-property mapping from source columns to ontology properties, stored as configuration | High | 4w |
| 8.4 | **Auto-Indexing Engine** | When source sync completes, automatically materialize source rows into ontology objects per type definitions | High | 4w |
| 8.5 | **Link Type System** | Define relationships between object types (1:1, 1:M, M:M) with foreign-key mapping, stored and queryable | High | 5w |
| 8.6 | **Link Resolution** | After object indexing, resolve link types to populate relationship tables | High | 3w |
| 8.7 | **Materialization Views** | Combined source + enrichment views for each object type, refreshable | Medium | 3w |
| 8.8 | **Ontology Migration from v1** | Migrate the 6 hardcoded domain types to the dynamic ontology system with zero downtime | High | 3w |
| 8.9 | **Property Value Formatting** | Configurable display formats, conditional formatting, render hints | Low | 2w |
| 8.10 | **Derived Properties** | Properties computed from other properties (e.g., `full_name = first_name + " " + last_name`) | Medium | 3w |

**Resource estimate:** 3-4 engineers, 33 engineering weeks

**Verification:** A user can create a new object type "Vendor" from a PostgreSQL table, define properties, set the primary key, and see the objects indexed automatically after the next sync. The user can also create a link type "Vendor→PurchaseOrder" and query linked objects.

**Dependencies:** Phase 7 (Universal Connector Framework) — must have source data to index.

---

## Phase 9: Multi-Modal Analytics Engine

**Goal:** Expand from basic monthly aggregation to a rich analytics surface comparable to Palantir's Quiver + Contour.

**Why now:** Once the ontology is dynamic (Phase 8), users need a generic way to query, aggregate, and visualize any object type. A fixed analytics engine cannot support user-defined types.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 9.1 | **Time Series Framework** | Generic time series storage and query engine (property × time → value) | Medium | 3w |
| 9.2 | **Object Set Operations** | Filter, intersect, union, difference on object sets with pagination | Medium | 3w |
| 9.3 | **Multi-Dimensional Aggregation** | Group-by on any property, pivot tables, drill-down/across | Medium | 4w |
| 9.4 | **Window Functions** | Running totals, moving averages, YoY/MoM comparisons | Low | 3w |
| 9.5 | **Statistical Functions** | Correlation, regression, distribution analysis, percentile | Medium | 3w |
| 9.6 | **Chart Data API** | Generic endpoint to request chart-ready data (bar, line, pie, scatter, heatmap) for any object type | Medium | 3w |
| 9.7 | **Saved Queries / Analysis Paths** | Users save and share analysis configurations | Medium | 2w |
| 9.8 | **Analytics Dashboard Builder** | Canvas-style workspace combining charts, tables, metrics | High | 5w |
| 9.9 | **Comparison Engine** | Compare any two object sets, time periods, or departments side-by-side | Medium | 3w |
| 9.10 | **Export Expansion** | Multi-sheet Excel, CSV, PDF report generation from analytics | Low | 3w |

**Resource estimate:** 2-3 engineers, 32 engineering weeks

**Verification:** A user can create a "Vendor Spend" analysis that groups PurchaseOrder objects by Vendor, sums amounts, and shows a bar chart, then save it and share it with another user.

**Dependencies:** Phase 8 (Dynamic Ontology Builder) — must have object types to aggregate.

---

## Phase 10: Application Builder & Widget System

**Goal:** Move from hardcoded dashboard pages to a composable widget-based application surface.

**Why now:** Once analytics are generic (Phase 9), users need a way to build their own dashboards without code changes. A widget system enables self-service analytics.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 10.1 | **Widget Registry** | Typed widget component system with configuration props, data binding, and event model | Medium | 3w |
| 10.2 | **Core Display Widgets** | Object Table, Object List, Object Card, Property List | Low | 3w |
| 10.3 | **Visualization Widgets** | Chart XY, Pie Chart, Metric Card, Pivot Table, Timeline, Map | Medium | 4w |
| 10.4 | **Filter Widgets** | Filter List, Dropdown, Date Picker, Text Search, Numeric Range | Medium | 3w |
| 10.5 | **Widget Canvas** | Drag-and-drop layout editor for arranging widgets on a page | High | 5w |
| 10.6 | **Variable System** | Shared state between widgets (selected object, date range, filters) for cross-widget interactivity | High | 4w |
| 10.7 | **Page/Routing System** | Multi-page dashboards with navigation, tabs, overlays | Medium | 3w |
| 10.8 | **Dashboard Templates** | Pre-built layouts for common HR analytics use cases | Low | 2w |
| 10.9 | **Object Detail Views** | Configurable detail page per object type showing properties, links, charts | Medium | 3w |
| 10.10 | **Dashboard Sharing** | Share dashboard configurations with other users | Low | 2w |

**Resource estimate:** 3-4 engineers, 32 engineering weeks

**Verification:** A user can create a new dashboard page, drag a Chart XY widget and a Filter List widget onto it, bind the chart to the "Vendor Spend" analysis, bind the filter to Vendor name, and see the chart update when the filter changes.

**Dependencies:** Phase 9 (Multi-Modal Analytics Engine) — must have chart data and object sets to display.

---

## Phase 11: AI Platform

**Goal:** Upgrade from "LLM narrates precomputed facts" to an AI platform with chatbots, semantic search, and AI-assisted analytics.

**Why now:** Once the ontology and analytics are rich (Phases 8-9), the AI can be grounded in structured data rather than raw text. This enables reliable, contextual AI assistance.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 11.1 | **Model Catalog** | Registry for multiple LLM providers (OpenAI, Anthropic, local models), with fallback chains | Medium | 3w |
| 11.2 | **Context Engineering Pipeline** | Build structured context objects from ontology data for LLM grounding | Medium | 4w |
| 11.3 | **AI Chat Interface** | Conversational UI for natural-language questions about data; answers grounded in facts | High | 5w |
| 11.4 | **Semantic Search** | Embedding-based search across ontology objects with hybrid keyword+semantic ranking | High | 5w |
| 11.5 | **AI-Generated Dashboards** | "Show me department spend trends for Q2" generates a widget layout | Very High | 5w |
| 11.6 | **AI Summaries v2** | Comparative summaries, temporal narratives, anomaly-focused explanations | Medium | 3w |
| 11.7 | **AIP Evals Framework** | Test harness for AI outputs: ground truth, consistency, hallucination detection | High | 4w |
| 11.8 | **AI Observability** | Trace every LLM call: prompt, response, latency, token usage, cost | Medium | 3w |

**Resource estimate:** 2-3 engineers + 1 ML specialist, 32 engineering weeks

**Verification:** A user can ask "Which departments had the highest spend variance last quarter?" and receive a grounded answer with chart references, or ask "Create a dashboard for vendor spend" and get a pre-built layout.

**Dependencies:** Phase 9 (Analytics Engine) — must have generic analytics to ground AI responses.

---

## Phase 12: Developer Platform & API

**Goal:** Expose Canopy as a platform that external apps and AI agents can build on.

**Why now:** Once the ontology, analytics, and AI are mature (Phases 8-11), external developers need programmatic access to build integrations, custom tools, and agent workflows.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 12.1 | **REST API v2** | Comprehensive versioned API (OpenAPI 3.1) covering ontology, analytics, exports, refresh | Medium | 4w |
| 12.2 | **Python SDK** | Auto-generated Python client from OpenAPI spec | Low | 2w |
| 12.3 | **TypeScript SDK** | Auto-generated TypeScript client for custom frontend apps | Low | 2w |
| 12.4 | **Webhook System** | Outbound webhooks for events (refresh complete, anomaly detected, threshold crossed) | Medium | 3w |
| 12.5 | **API Key Management** | Per-user/per-tenant API key generation, rotation, and scope management | Medium | 3w |
| 12.6 | **Custom Widget SDK** | Allow external React components to be embedded as dashboard widgets | High | 4w |
| 12.7 | **MCP Server** | Model Context Protocol server for AI agents to discover and query Canopy ontology | Medium | 3w |

**Resource estimate:** 2 engineers, 21 engineering weeks

**Verification:** An external developer can generate an API key, use the Python SDK to query "Vendor" objects, filter by region, and receive typed results. An AI agent can use the MCP server to list object types and query properties.

**Dependencies:** Phase 8 (Dynamic Ontology) — must have a programmable ontology to expose.

---

## Phase 13: Automation & Observability

**Goal:** Add condition-based automation and production-grade observability.

**Why now:** Once the platform is rich (Phases 7-12), users need automated alerts, scheduled reports, and visibility into system health. This is the capstone for production reliability.

**Deliverables:**

| # | Deliverable | Description | Risk | Effort |
|---|---|---|---|---|
| 13.1 | **Automation Engine** | Condition types (time, data-change, threshold) triggering effects (notifications, exports, refresh) | High | 5w |
| 13.2 | **Notification System** | Email, in-app, and webhook notifications with templating | Medium | 3w |
| 13.3 | **Alert Rules** | Threshold-based alerts on any metric with configurable severity | Medium | 3w |
| 13.4 | **Workflow Lineage** | Full execution graph: connector→ingest→clean→index→aggregate→detect→summarize→export | Medium | 4w |
| 13.5 | **Data Health Dashboard** | Per-connector, per-dataset, per-object-type freshness, quality, completeness monitoring | Medium | 4w |
| 13.6 | **Audit Log** | Immutable log of all system actions: refreshes, exports, config changes, user logins | Medium | 3w |
| 13.7 | **Cost Attribution** | Track LLM token usage, compute cost, storage cost per tenant | Low | 2w |

**Resource estimate:** 2 engineers, 24 engineering weeks

**Verification:** A user can set an alert: "Notify me when department spend exceeds $100k in a month." The system detects the condition, sends an email, and logs the event in the audit log. The user can view the workflow lineage for the refresh that triggered it.

**Dependencies:** Phase 12 (Developer Platform) — webhooks needed for notifications. Phase 11 (AI Platform) — cost tracking for LLM usage.

---

## Timeline

```
        Q4 2026   Q1 2027   Q2 2027   Q3 2027   Q4 2027   Q1 2028   Q2 2028   Q3 2028   Q4 2028   Q1 2029   Q2 2029   Q3 2029   Q4 2029   Q1 2030
Phase 7  ████████  ████████  ████████  ████████
Phase 8            ████████  ████████  ████████  ████████  ████████
Phase 9                      ████████  ████████  ████████  ████████  ████████
Phase 10                                         ████████  ████████  ████████  ████████  ████████
Phase 11                                                   ████████  ████████  ████████  ████████  ████████
Phase 12                                                                         ████████  ████████  ████████  ████████
Phase 13                                                                                   ████████  ████████  ████████  ████████
```

### Quarter-by-Quarter View

| Quarter | Primary Focus | Key Milestones |
|---|---|---|
| **Q4 2026** | Phase 7 kickoff | Connector base class, JDBC adapter, file expansion |
| **Q1 2027** | Phase 7 complete, Phase 8 start | Connector wizard UI, sync policies, health monitoring; ontology schema |
| **Q2 2027** | Phase 8 early | Object type editor, backing datasource binding, auto-indexing |
| **Q3 2027** | Phase 8 mid | Link types, link resolution, materialization views |
| **Q4 2027** | Phase 8 complete, Phase 9 start | Ontology migration, derived properties; time series framework |
| **Q1 2028** | Phase 9 early | Object set operations, multi-dimensional aggregation, window functions |
| **Q2 2028** | Phase 9 complete, Phase 10 start | Chart data API, dashboard builder; widget registry, core widgets |
| **Q3 2028** | Phase 10 mid | Visualization widgets, filter widgets, widget canvas |
| **Q4 2028** | Phase 10 complete, Phase 11 start | Variable system, page routing, templates; model catalog, context pipeline |
| **Q1 2029** | Phase 11 mid | AI chat interface, semantic search, AI-generated dashboards |
| **Q2 2029** | Phase 11 complete, Phase 12 start | AI evals, observability; REST API v2, Python/TypeScript SDKs |
| **Q3 2029** | Phase 12 mid | Webhook system, API key management, custom widget SDK |
| **Q4 2029** | Phase 12 complete, Phase 13 start | MCP server; automation engine, notifications, alert rules |
| **Q1 2030** | Phase 13 complete | Workflow lineage, data health, audit log, cost attribution |

---

## Resource Summary

### Engineering Weeks by Phase

| Phase | Weeks | Engineers |
|---|---|---|
| 7. Universal Connector Framework | 22 | 2-3 |
| 8. Dynamic Ontology Builder | 33 | 3-4 |
| 9. Multi-Modal Analytics Engine | 32 | 2-3 |
| 10. Application Builder & Widget System | 32 | 3-4 |
| 11. AI Platform | 32 | 2-3 + ML |
| 12. Developer Platform & API | 21 | 2 |
| 13. Automation & Observability | 24 | 2 |
| **Total** | **196** | **Peak 4-5** |

### Team Composition

- **Backend Engineers (2-3):** FastAPI, Python, PostgreSQL, async jobs
- **Frontend Engineers (2-3):** Next.js, TypeScript, React, drag-and-drop
- **ML/AI Engineer (1):** LLM integration, embeddings, semantic search
- **DevOps/Platform (1):** Infrastructure, monitoring, security (part-time)

### Sustaining Engineering

Existing v1-v6 features require ongoing maintenance. Budget 10-15% of capacity per quarter for:
- Bug fixes and regressions
- Dependency updates (Next.js, FastAPI, PostgreSQL)
- Security patches
- Performance optimization

### Total Cost of Ownership (Rough Estimate)

| Category | Cost |
|---|---|
| Engineering (196 weeks × $3k/week blended rate) | ~$588k |
| Infrastructure (cloud, storage, LLM API costs) | ~$50k/year |
| Design/UX (widget system, dashboard builder) | ~$40k |
| Security audit (Phase 13) | ~$20k |
| **3.5-year total** | **~$698k** |

---

## Decision Points

Before committing to this roadmap, the following decisions must be made:

### 1. Action Boundary

**Question:** Should Canopy support explicit, audited actions against approved connected systems, or stay read-only forever?

**Options:**
- **A. Support controlled actions now.** Explicit permissions, approvals, audit logs, and connector-scoped action policies. Preferred for approved operational workflows.
- **B. Stay read-only forever.** Preserve maximum simplicity, but block write or approval workflows in the platform.
- **C. Allow actions only to Canopy-owned tables, not source systems.** User edits are stored in Canopy's application DB and materialized into views, but never pushed upstream.

**Recommendation:** A for Phases 7-13.

### 2. Scale Target

**Question:** Palantir handles petabyte-scale data and thousands of users. What is Canopy's target scale?

**Options:**
- **A. Small-medium enterprise (< 1000 users, < 1TB data).** Current monolith architecture is sufficient. No need for distributed compute.
- **B. Large enterprise (< 10,000 users, < 10TB data).** May need read replicas, caching layers, and background job scaling.
- **C. Enterprise platform (10,000+ users, 100TB+ data).** Requires distributed compute (Spark/Flink), object storage, and microservices.

**Recommendation:** A for Phases 7-13. The monolith should be designed to scale to B with horizontal scaling, but C is out of scope.

### 3. HR Focus vs. General Platform

**Question:** Canopy started as executive HR spend intelligence. Should it stay HR-centric or become a general-purpose data operating system?

**Options:**
- **A. Stay HR-focused.** The ontology builder is scoped to HR/finance/operations objects. The application builder provides HR-specific templates. AI is trained on HR analytics patterns.
- **B. Expand to general organizational analytics.** The ontology builder is generic. Any domain can define object types. The application builder is domain-agnostic.
- **C. Hybrid: HR core with extensible plugin model.** The base platform is HR-focused, but a plugin system allows custom domains and object types.

**Recommendation:** B for the platform infrastructure (connector, ontology, analytics), but A for the default templates, AI prompts, and onboarding experience. Users can opt into general-purpose use.

### 4. AI Ambition

**Question:** How deeply should AI be integrated?

**Options:**
- **A. Surface-level assistant.** Chat interface for asking questions about data, generating summaries, and suggesting analyses. AI does not build dashboards or modify configurations.
- **B. Deep integration.** AI can generate dashboards, configure alerts, suggest ontology mappings, and write connector configurations. AI is a co-builder.
- **C. Autonomous agents.** AI agents can trigger refreshes, generate reports, and notify stakeholders without human intervention.

**Recommendation:** A for Phase 11. B for Phase 11.5 (AI-generated dashboards). C is out of scope for Phases 7-13.

### 5. Build vs. Buy/Integrate

**Question:** For connectors (Phase 7), should Canopy build its own framework or integrate with existing ETL tools?

**Options:**
- **A. Build everything.** Custom connector framework, custom sync engine, custom scheduling. Maximum control, maximum engineering cost.
- **B. Integrate with open-source ETL.** Use Apache Airflow for scheduling, dbt for transforms, Airbyte for connectors. Canopy focuses on the ontology and analytics layers.
- **C. Hybrid: Build core connectors, integrate for exotic sources.** Build JDBC, REST, and file connectors natively. For SAP, Salesforce, etc., integrate with Fivetran or similar.

**Recommendation:** A for core connectors (JDBC, REST, file) because they are tightly coupled to Canopy's ontology and sync pipeline. C for exotic sources if needed.

---

## Success Metrics

### Phase 7: Universal Connector Framework

| Metric | Target | Measurement |
|---|---|---|
| Connector types supported | ≥ 5 | JDBC, REST, file (CSV/JSON/Parquet), plus 2 more |
| New connection setup time | < 5 minutes | Time from UI start to first sync |
| Sync success rate | > 95% | Percentage of scheduled syncs completing without error |
| Connector health coverage | 100% | All connectors have health checks and status dashboards |

### Phase 8: Dynamic Ontology Builder

| Metric | Target | Measurement |
|---|---|---|
| Object types created by users | ≥ 10 | Count of user-created types (excluding migrated v1 types) |
| Ontology creation time | < 10 minutes | Time from selecting a source table to indexed objects |
| Link type coverage | ≥ 50% | Percentage of object types with at least one link |
| Migration downtime | 0 minutes | Zero downtime during v1→v8 ontology migration |

### Phase 9: Multi-Modal Analytics Engine

| Metric | Target | Measurement |
|---|---|---|
| Saved analyses | ≥ 50 | Count of user-saved analysis configurations |
| Dashboard load time | < 2 seconds | P95 load time for analytics dashboards |
| Chart types supported | ≥ 8 | Bar, line, pie, scatter, heatmap, table, pivot, metric card |
| Export formats | ≥ 3 | Excel, CSV, PDF |

### Phase 10: Application Builder & Widget System

| Metric | Target | Measurement |
|---|---|---|
| User-created dashboards | ≥ 20 | Count of dashboards created by non-engineers |
| Widget types | ≥ 15 | Core display + visualization + filter + event widgets |
| Cross-widget interaction | 100% | All widgets can bind to shared variables |
| Template usage | ≥ 30% | Percentage of new dashboards created from templates |

### Phase 11: AI Platform

| Metric | Target | Measurement |
|---|---|---|
| AI answer accuracy | > 85% | Grounded answers validated against deterministic metrics |
| AI response latency | < 5 seconds | P95 time from question to grounded answer |
| Semantic search relevance | > 80% | Top-5 precision for object queries |
| AI-generated dashboards accepted | > 50% | Percentage of AI-generated layouts kept by users |

### Phase 12: Developer Platform & API

| Metric | Target | Measurement |
|---|---|---|
| API endpoints | ≥ 50 | Count of documented REST API endpoints |
| SDK downloads | ≥ 100 | Combined Python + TypeScript SDK downloads |
| External integrations | ≥ 5 | Count of third-party tools using Canopy API |
| MCP tool coverage | ≥ 20 | Count of MCP tools exposing ontology operations |

### Phase 13: Automation & Observability

| Metric | Target | Measurement |
|---|---|---|
| Automation rules | ≥ 20 | Count of active condition→effect rules |
| Alert response time | < 1 minute | Time from threshold breach to notification sent |
| Workflow lineage coverage | 100% | All refresh jobs traced end-to-end |
| Audit log retention | 90 days | Immutable log retention period |

---

## Risk Register

| # | Risk | Phase | Impact | Likelihood | Mitigation |
|---|---|---|---|---|---|
| 1 | **Dynamic ontology migration fails** | 8 | High | Medium | Run parallel migration with rollback plan; keep v1 tables until verified |
| 2 | **AI hallucinations damage trust** | 11 | High | Medium | Ground all AI responses in deterministic facts; eval framework catches errors before release |
| 3 | **Widget canvas UX is too complex** | 10 | High | Medium | Start with simple layout presets; advanced drag-and-drop is optional |
| 4 | **Connector security vulnerabilities** | 7 | High | Low | Encrypt credentials at rest; use connection pooling; audit all connector queries |
| 5 | **Performance degrades with dynamic types** | 8-9 | Medium | Medium | Query plans must be tenant-scoped; index property columns; monitor query latency |
| 6 | **Developer platform adoption is low** | 12 | Medium | Low | Partner with early adopters; provide SDK samples; dogfood the API internally |
| 7 | **Team bandwidth insufficient** | All | High | Medium | Prioritize Phase 7-8; defer 10-13 if needed; hire specialist for Phase 11 |
| 8 | **Technical debt from v1-v6** | 7-8 | Medium | High | Budget 15% of each phase for refactoring; enforce test coverage gates |
| 9 | **Data privacy compliance (GDPR, SOC2)** | 7-13 | High | Low | Audit logging in Phase 13; data retention policies; encryption at rest and in transit |
| 10 | **User resistance to self-service analytics** | 10 | Medium | Medium | Provide templates and training; keep existing hardcoded dashboards as defaults |
| 11 | **LLM API costs spiral** | 11 | Medium | Medium | Rate limiting per tenant; model fallback chains; caching of common queries |
| 12 | **Dependency on open-source libraries** | 7-12 | Medium | Medium | Pin versions; maintain fork for critical libs; have migration plans |

---

## Appendix A: Technology Stack Recommendations

### Phase 7-8: Connector + Ontology

| Component | Current | Recommended |
|---|---|---|
| Database | PostgreSQL | PostgreSQL (no change) |
| Async jobs | Background worker | Celery + Redis (or keep existing) |
| Schema inference | Custom | Integrate with `sqlalchemy` + `pandas` for JDBC |
| File parsing | Custom | `pandas` for CSV/JSON, `pyarrow` for Parquet/Avro |

### Phase 9: Analytics

| Component | Current | Recommended |
|---|---|---|
| Time series | None | InfluxDB or TimescaleDB (PostgreSQL extension) |
| Query engine | SQLAlchemy | SQLAlchemy + query builder for dynamic aggregations |
| Chart data | Hardcoded endpoints | Generic chart query endpoint with JSON schema |

### Phase 10: Widgets

| Component | Current | Recommended |
|---|---|---|
| Drag-and-drop | None | `react-dnd` or `react-grid-layout` |
| Chart library | Recharts | Recharts + `visx` for custom visualizations |
| State management | React context | Zustand or Jotai for cross-widget variables |

### Phase 11: AI

| Component | Current | Recommended |
|---|---|---|
| LLM provider | Single provider | Multi-provider with fallback (OpenAI, Anthropic, local) |
| Embeddings | None | `sentence-transformers` or OpenAI embeddings API |
| Vector DB | None | `pgvector` (PostgreSQL extension) or Pinecone |
| Context management | None | Structured context objects with deterministic grounding |

### Phase 12: API

| Component | Current | Recommended |
|---|---|---|
| API spec | None | FastAPI auto-generates OpenAPI; enhance with `fastapi-filter` |
| SDK generation | None | `openapi-generator` for Python/TypeScript clients |
| Webhooks | None | FastAPI background tasks + Celery for delivery |
| MCP | None | Custom MCP server using `mcp` Python SDK |

### Phase 13: Observability

| Component | Current | Recommended |
|---|---|---|
| Monitoring | Basic logs | Prometheus + Grafana for metrics |
| Tracing | None | OpenTelemetry + Jaeger for distributed tracing |
| Audit log | None | Append-only PostgreSQL table with tamper-proof hashing |

---

## Appendix B: Cross-Reference to Architecture Documents

| Document | Role |
|---|---|
| `ARCHITECTURE.md` | Source of truth for system intent, boundaries, and rules |
| `DESIGN.md` | Visual design source of truth |
| `QUICKSTART.md` | Setup, run, test, lint |
| `doc/codebase-map.md` | Current codebase snapshot |
| `doc/palantir-canopy-comparison.md` | Detailed comparison with Palantir Foundry |
| `doc/canopy-enhancement-roadmap.md` | This document — Phase 7-13 plan |

---

## Document Notes

- **Status:** Draft
- **Date:** 2026-06-09
- **Author:** AI Agent (Canopy Intelligence)
- **Next Review:** Before Phase 7 kickoff
- **Change Log:**
  - 2026-06-09: Initial draft — all phases defined with deliverables, estimates, and risks

---

[Previous: Palantir-Canopy Comparison](palantir-canopy-comparison.md)
