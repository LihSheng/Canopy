# Palantir Foundry vs Canopy Intelligence: Architecture Comparison

## Executive Summary

This document compares Palantir Foundry's enterprise data operating system with Canopy Intelligence's current architecture. The goal is to understand the gaps between a mature, general-purpose data platform and Canopy's current state, so that Canopy's enhancement roadmap can be informed by proven patterns while preserving its deliberate design choices.

**Palantir Foundry** is a full-stack enterprise data platform that connects to any source, builds a semantic object layer (Ontology), provides low-code and pro-code application builders, and embeds AI throughout the stack. It serves thousands of users across industries from defense to healthcare to manufacturing.

**Canopy Intelligence** is an executive HR spend intelligence platform built as a modular monolith. It reads from an internal database, normalizes data into a fixed ontology, computes monthly analytics and anomalies, and presents dashboards plus AI-generated summaries. It is currently read-only and deterministic-first.

The comparison is not a proposal to copy Palantir. It is a map of what Canopy could become if it chooses to expand from a single-domain, single-tenant read-only product into a multi-source, multi-tenant data operating system.

---

## Table of Contents

1. [Palantir Foundry Architecture](#palantir-foundry-architecture)
2. [Canopy Intelligence Architecture](#canopy-intelligence-architecture)
3. [Data Flow Comparison](#data-flow-comparison)
4. [Ontology-Data Communication Comparison](#ontology-data-communication-comparison)
5. [Data Population & Visualization](#data-population--visualization)
6. [Feature Comparison Matrix](#feature-comparison-matrix)
7. [Architecture Incompatibilities](#architecture-incompatibilities)
8. [Key Takeaways](#key-takeaways)

---

## Palantir Foundry Architecture

Palantir Foundry is organized into three primary layers: the Data Layer, the Ontology Layer, and the Application Layer. Below these sit the Analytics, AI Platform, Automation, and Observability systems.

### Data Layer

Raw data enters through **Connectors** (200+ types: databases, APIs, cloud storage, enterprise systems like SAP). Data is pulled or pushed into **Datasets** stored as Apache Iceberg tables. Each dataset maintains versioning, branching, and full history.

```
Source Systems (DBs, APIs, SAP, S3, etc.)
    ↓
Connectors (200+ types, agents, private links)
    ↓
Syncs (batch, streaming, CDC, file upload)
    ↓
Datasets (Apache Iceberg, versioned, branched)
    ↓
Transforms (Pipeline Builder visual, or Python/SQL/Java code)
    ↓
Clean Datasets (output of transforms, with lineage)
```

Key concepts:
- **Dataset**: Wrapper around tabular or unstructured files. Structured datasets have schemas. All maintain history.
- **Transform**: Code or visual logic that processes input datasets to produce output datasets. Written in Python (PySpark/Pandas/Polars), SQL, or Java.
- **Pipeline Builder**: Point-and-click tool for building data pipelines with health checks, type-safe transforms, and LLM assistance.
- **Code Repositories**: Web-based IDE with Git for production-grade transforms.
- **Incremental pipelines**: Process only changed rows/files, not full recompute.
- **Streaming**: Near real-time via Flink.
- **Data lineage**: Complete tracking of input datasets → logic → output datasets.
- **Branching**: Version control for datasets and pipelines, parallel development with merge proposals.

### Ontology Layer

The Ontology is the semantic layer that maps raw data to real-world concepts. It transforms rows into objects, columns into properties, and relationships into links.

```
Clean Datasets
    ↓
Object Types (schema definitions for real-world entities)
    ├─ Properties (attributes with types, primary key, title)
    ├─ Backing Datasource (dataset providing the rows)
    ├─ Link Types (relationships between object types)
    ├─ Interfaces (polymorphic shared-property contracts)
    ├─ Action Types (declarative mutations users can make)
    └─ Functions (server-side business logic)
    ↓
Ontology Objects (indexed from dataset rows via Funnel pipelines)
    ↓
Applications (Workshop, Slate, OSDK, custom apps)
```

Key concepts:
- **Object Type**: Schema definition for real-world entities (e.g., `Employee`, `Order`). Defines properties, primary key, title, and backing dataset(s).
- **Link Type**: Relationship between object types with cardinality (one-to-one, one-to-many, many-to-many). Uses foreign keys or join tables.
- **Interface**: Abstract type describing shared properties across multiple object types. Enables polymorphic workflows.
- **Action Type**: Declarative definition of user mutations (create/edit/delete objects). Includes parameters, rules, side effects (notifications, webhooks), and submission criteria.
- **Function**: Server-side code (TypeScript or Python) that reads ontology data, performs computation, and can make ontology edits.
- **Indexing**: Automatic pipeline (Funnel batch or Funnel streaming) that transforms dataset rows into ontology objects when backing datasets update.
- **Materialization**: Combined dataset of source data + user edits, used for downstream pipelines or downloads.
- **Multi-datasource object types (MDOs)**: One object type backed by multiple datasets, reconciled by primary key.

### Application Layer

Applications consume data from the Ontology and Datasets layers.

**Workshop** — low-code, object-oriented application builder. 60+ widgets (tables, charts, maps, forms, buttons, AIP chatbots, media). Uses drag-and-drop canvas with variables, events, and layouts.

**Slate** — custom HTML/CSS/JS drag-and-drop application builder. Direct JavaScript access to Ontology and Functions via API calls.

**OSDK (Ontology SDK)** — Auto-generated type-safe SDKs (TypeScript, Python, Java, OpenAPI) for building custom applications. Includes object queries, link traversal, action execution, real-time subscriptions.

**Carbon** — Curated workspace experiences for specific user groups. Combines multiple applications and resources into a single focused interface.

**Pilot** — AI-powered application builder that generates ontology, design specs, frontend code, and seed data from natural language prompts.

### Analytics Layer

**Quiver** — Object-driven and time series analysis. 200+ card types. Supports dashboards, link traversal, time series formulas, anomaly detection, and machine learning.

**Contour** — Point-and-click tabular analysis. Best for large datasets (100k+ rows). Visual transforms, joins, aggregations, dashboards.

**Object Explorer** — Search and analysis tool for browsing ontology objects. Keyword search, property-based filters, bulk actions, export.

**Insight** — Step-by-step analysis with link traversal, aggregations, visualizations, maps, SQL queries, and writeback.

**Notepad** — Object-aware rich-text editor. Embeds charts and tables from other tools. Template-based report generation.

**Fusion** — Spreadsheet application with ontology integration. Writeback from spreadsheets to datasets.

### AI Platform (AIP)

**AIP Chatbot Studio** — Build interactive LLM assistants with retrieval context (Ontology objects, documents, function outputs) and tools (actions, object queries, functions, commands).

**AIP Logic** — No-code visual block-based environment for building LLM-powered functions that can query and edit the Ontology.

**AIP Assist** — In-platform LLM assistant for navigation and understanding.

**AIP Evals** — Testing framework for evaluating LLM outputs, handling non-determinism.

**Semantic Search** — Embedding-based search across documents and ontology objects.

### Automation Layer

**Automate** — Condition-based triggers (time, data changes, thresholds) with effects (execute actions, call functions, send notifications, trigger builds).

**Foundry Rules** — Business rule engine with ontology-driven workflows.

**Autopilot** — Task orchestration and workflow management.

### Observability Layer

**Data Health** — Monitoring views and health checks for datasets, builds, functions, actions, and automations.

**Workflow Lineage** — Interactive execution graph with 7-day history, trace views, and log search.

**AIP Observability** — Trace views for LLM calls, metrics, and log search.

---

## Canopy Intelligence Architecture

Canopy is built as a modular monolith with asynchronous background jobs.

### Stack

- **Frontend**: Next.js + TypeScript
- **Backend**: FastAPI + Python
- **Primary DB**: Application database (normalized ontology, analytics, auth, refresh metadata)
- **Source System**: Internal database, read-only
- **Jobs**: Background worker for scheduled sync and summary generation
- **AI**: LLM provider for natural-language summaries
- **Export**: Excel export library
- **Auth**: Simple email/password for v1

### Core Modules (v1-v6)

1. **Web Application** — Executive dashboard, login, summary metrics, trend charts, anomaly cards, drill-down, export, refresh
2. **Application API** — Typed HTTP APIs, thin routing layer
3. **Identity and Access** — Email/password auth, sessions
4. **Source Sync** — Read from internal DB, pull HR/spend entities, read-only
5. **Semantic / Ontology Mapping** — 6 fixed object types: Department, Employee, CostCenter, ExpenseClaim, PayrollExpense, BudgetCode
6. **Analytics Aggregation** — Monthly spend views, rankings, deltas, breakdowns
7. **Anomaly Detection** — Department spend change detection, claim expense patterns
8. **Insight Generation** — LLM narrates precomputed facts into executive summaries
9. **Reporting and Export** — Excel exports aligned with dashboard data
10. **Refresh Orchestration** — Scheduled daily sync, manual refresh, job sequencing
11. **Application Data Store** — PostgreSQL with logical zones: staging, ontology, analytics, insight cache, metadata
12. **Extension Modules (v2-v6)**:
    - v2: Dashboard shell, navigation, tenant switcher
    - v3: Ingestion, cleaning, normalization, upload wizard, lineage graph
    - v4: Workspace, dataset, source catalog, preview
    - v5: Multi-tenant platform, tenant access, RLS, provisioning
    - v6: Data connection workbench, MySQL, PostgreSQL, static file, dataset versioning

### Data Flow

```
Source Sync (internal DB)
    ↓
Staging / Source Snapshot
    ↓
Ontology Mapping (6 fixed types)
    ↓
Analytics Aggregation
    ↓
Anomaly Detection
    ↓
Insight Generation (LLM narrates)
    ↓
Dashboard / Export / AI Summary
```

### Three Non-Negotiable Rules

1. **Never writes back to source system.** Read-only input.
2. **Deterministic analytics decide. The LLM narrates.** No invented metrics.
3. **Dashboard, export, and AI use same snapshot.** No mismatched data.

### Guardrails

- Tenant-aware seams even when single-tenant
- Storage routing via repository boundaries
- Source-specific schema isolated in sync readers
- No hidden global mutable state
- Phase labels (`v2`, `v3`) only in docs, never in runtime code

---

## Data Flow Comparison

### Palantir Foundry

```
Source Systems (DBs, APIs, SAP, S3, etc.)
    ↓
Connectors (200+ types, agents, CDC)
    ↓
Datasets (Iceberg, versioned, branched)
    ↓
Transforms (Python/SQL/Java, visual or code)
    ↓
Clean Datasets
    ↓
Ontology Indexing (Funnel batch/streaming)
    ├─ Object Types (properties, primary key, backing dataset)
    ├─ Link Types (relationships, cardinality)
    ├─ Interfaces (polymorphic contracts)
    └─ Functions (server-side logic)
    ↓
Applications (Workshop, Slate, OSDK, Carbon)
    ├─ Widgets (60+ types, data-bound)
    ├─ Events (interactivity)
    ├─ Variables (shared state)
    └─ Actions (user mutations, writeback)
    ↓
Analytics (Quiver, Contour, Object Explorer, Notepad, Fusion)
    ↓
AI (AIP Chatbots, AIP Logic, semantic search)
    ↓
Automation (Automate, rules, triggers)
    ↓
Observability (Data Health, Workflow Lineage)
```

### Canopy Intelligence

```
Source System (internal DB, read-only)
    ↓
Source Sync (6 entity readers)
    ↓
Staging / Source Snapshot
    ↓
Ontology Mapping (6 fixed domain types)
    ├─ Department
    ├─ Employee
    ├─ CostCenter
    ├─ ExpenseClaim
    ├─ PayrollExpense
    └─ BudgetCode
    ↓
Analytics Aggregation (monthly views)
    ├─ Total payroll spend by month
    ├─ Total claim spend by month
    ├─ Department rankings
    ├─ Month-over-month deltas
    └─ Claim type breakdowns
    ↓
Anomaly Detection (department changes, claim patterns)
    ↓
Insight Generation (LLM narrates precomputed facts)
    ↓
Dashboard (summary, trends, drill-down, anomalies)
    ├─ Export (Excel)
    └─ AI Summary
```

### Key Differences

| Aspect | Palantir | Canopy |
|---|---|---|
| Source count | 200+ connector types | 3 (internal DB, MySQL, PostgreSQL, static file) |
| Dataset versioning | Apache Iceberg, branching, time travel | Immutable dataset versioning (v6) |
| Transform tool | Pipeline Builder (visual) + Code Repos | Cleaning engine, normalization pipeline |
| Ontology types | User-defined, dynamic, polymorphic | 6 fixed types, hardcoded |
| Ontology-data binding | Declarative backing datasource + auto-indexing | Manual mappers per entity family |
| Links | Full link type system (1:1, 1:M, M:M) | None — flat objects |
| Mutations | Action types, function-backed edits | None — read-only |
| Application builder | Workshop (low-code, 60+ widgets) | Next.js dashboard (hardcoded pages) |
| Analytics | Quiver, Contour, Object Explorer, Notepad | Monthly aggregation, rankings, anomalies |
| AI depth | Chatbots, logic, evals, semantic search | LLM narrates precomputed facts |
| Automation | Automate (condition→effect), rules | Refresh orchestration |
| Export | Power BI, Tableau, ODBC, REST, Excel, PDF | Excel only |
| Observability | Data Health, Workflow Lineage, traces | Refresh status, job tracking |
| Developer API | OSDK, REST, MCP, Python/R SDKs | None beyond internal API |

---

## Ontology-Data Communication Comparison

### Palantir: Declarative Backing Datasource

In Palantir, the Ontology communicates with data sources through a **declarative backing datasource model**:

1. **Object Type Declaration**: When creating an object type, the builder explicitly declares which dataset(s) back the object's properties.
2. **Property Mapping**: Each property maps to a column in the backing dataset. The primary key column becomes the object identifier.
3. **Funnel Indexing**: When the backing dataset is updated (via a sync or transform build), Funnel indexing pipelines automatically process the dataset rows and create/update/delete ontology objects.
4. **One Row = One Object**: Direct mapping. Each row in the backing dataset becomes one instance of the object type.
5. **Link Resolution**: After object indexing, link types are resolved by matching foreign key columns to primary keys of target objects.
6. **Materialization**: For object types with user edits, a materialization pipeline combines the backing dataset with edit history to produce a unified dataset.
7. **Streaming Indexing**: For real-time use cases, streaming indexing pipelines process changelog events as they arrive.

This is **configuration-driven**: the builder sets up the object type and its backing datasource, and the platform handles the sync automatically.

### Canopy: Manual Mapper Chain

In Canopy, the Ontology communicates with data sources through a **manual mapper chain**:

1. **Source Sync Readers**: Only the sync module knows the raw source schema. Each source entity family has its own reader.
2. **Source Staging**: Raw records are written to staging or source snapshot tables.
3. **Ontology Mappers**: Each source entity family has a dedicated mapper that transforms raw rows into normalized business objects.
4. **Fixed Schema**: The 6 domain types are hardcoded in code. There is no dynamic configuration for new object types.
5. **No Link System**: Objects are independent. Relationships are handled at query time by matching IDs, not by a persistent link type system.
6. **No Indexing Pipeline**: The normalization happens during the refresh job, not through an automatic indexing pipeline.
7. **No Materialization**: The normalized ontology tables are the materialized view. There is no separate materialization layer for user edits (since Canopy is read-only).

This is **code-driven**: adding a new object type requires writing a new mapper, adding new schema tables, and updating the analytics aggregators.

### Comparison

| Aspect | Palantir | Canopy |
|---|---|---|
| **Binding style** | Declarative configuration | Code-based mappers |
| **Object type creation** | UI-driven, no code required | Requires code changes |
| **Auto-indexing** | Yes, via Funnel pipelines | No, manual refresh job |
| **Link types** | Declarative, persisted | Not supported |
| **Multi-datasource objects** | Supported | Not supported |
| **Streaming sync** | Yes, Funnel streaming | Deferred (real_time mode defined, CDC not implemented) |
| **Materialization** | Source + user edits combined | Source only (read-only) |
| **Schema evolution** | Supported, with migration tools | Requires code changes + Alembic migrations |
| **User-driven ontology** | Yes — non-technical users can define object types | No — ontology is developer-maintained |

---

## Data Population & Visualization

### Palantir: 7 Data Input Paths

| # | Path | Description | Canopy Equivalent |
|---|---|---|---|
| 1 | **Batch Sync** | Scheduled or manual pull from 200+ connectors | Source Sync (scheduled, manual) |
| 2 | **Streaming Sync** | Near real-time via Kafka, Kinesis, CDC | Not implemented (deferred) |
| 3 | **File Upload** | Excel, CSV, JSON, Parquet, images, PDFs, videos | Static file import (v6) |
| 4 | **Webhook/Listener** | HTTPS, WebSocket, Email endpoints for external push | Not implemented |
| 5 | **Push Ingestion** | Direct API push into streams | Not implemented |
| 6 | **Fusion Spreadsheet** | Manual data entry in spreadsheet with sync to dataset | Not implemented |
| 7 | **External Transforms** | Custom compute containers that write back to Foundry | Not implemented |

### Palantir: 12 Data Output/Visualization Paths

| # | Path | Description | Canopy Equivalent |
|---|---|---|---|
| 1 | **Workshop** | Low-code app builder, 60+ widgets | Dashboard pages (hardcoded) |
| 2 | **Slate** | Custom HTML/CSS/JS drag-and-drop apps | Not implemented |
| 3 | **OSDK Apps** | TypeScript/Python/Java custom apps | Not implemented |
| 4 | **Contour** | Tabular analysis + dashboards | Not implemented |
| 5 | **Quiver** | Object + time series analysis, dashboards | Not implemented |
| 6 | **Object Explorer** | Search/browse ontology objects | Entity pages (partial) |
| 7 | **Insight** | Step-by-step analysis with writeback | Not implemented |
| 8 | **Notepad** | Rich documents with embedded analytics | Not implemented |
| 9 | **Fusion** | Ontology-backed spreadsheet | Not implemented |
| 10 | **Map / Vertex** | Geospatial + graph visualization | Not implemented |
| 11 | **3rd-party BI** | Power BI, Tableau, ODBC, REST APIs | Not implemented |
| 12 | **Carbon** | Curated workspace experiences | Not implemented |

### Canopy: 3 Data Input Paths

| # | Path | Description |
|---|---|---|
| 1 | **Internal DB Sync** | Read-only scheduled sync from internal PostgreSQL |
| 2 | **Connection Wizard** | MySQL and PostgreSQL connections (v6) |
| 3 | **Static File Import** | Excel/CSV upload, profiling, cleaning, mapping (v3-v6) |

### Canopy: 4 Data Output/Visualization Paths

| # | Path | Description |
|---|---|---|
| 1 | **Dashboard** | Summary metrics, trend charts, anomaly cards, drill-down |
| 2 | **Entity Pages** | Department detail, employee list, claim types |
| 3 | **Export** | Excel workbook with executive summary and breakdowns |
| 4 | **AI Summary** | Natural-language summary of precomputed facts |

---

## Feature Comparison Matrix

| # | Capability | Palantir Foundry | Canopy (v1-v6) | Gap |
|---|---|---|---|---|
| 1 | **Source Connectivity** | 200+ connectors, CDC, streaming, webhooks, agents, listeners | Read-only internal DB, MySQL, PostgreSQL, static file | 🔴 CRITICAL |
| 2 | **Connector Framework** | Extensible with agent workers, private links, SAP add-ons | Hardcoded source types (v6) | 🔴 CRITICAL |
| 3 | **Data Ingestion** | Pipeline Builder, transforms, syncs, schedules | Source Sync readers, raw import capture | 🟡 LARGE |
| 4 | **Data Pipeline/Transform** | Pipeline Builder (visual), Python/SQL/Java, incremental, streaming | Cleaning engine, normalization pipeline | 🟡 LARGE |
| 5 | **Dataset Management** | Apache Iceberg, versioning, branching, transactions | Immutable dataset versioning (v6), lineage graph | 🟢 MODERATE |
| 6 | **Ontology (Object Types)** | User-defined, dynamic, polymorphic, with backing datasources | 6 fixed domain types (Department, Employee, etc.) | 🔴 CRITICAL |
| 7 | **Ontology (Link Types)** | 1:1, 1:M, M:M, traversable, object-backed links | Not supported | 🔴 CRITICAL |
| 8 | **Ontology (Interfaces)** | Polymorphic shared-property contracts | Not supported | 🟡 LARGE |
| 9 | **Ontology (Action Types)** | Declarative mutations with parameters, rules, side effects | Not supported (read-only) | 🟡 DELIBERATE |
| 10 | **Ontology (Functions)** | TypeScript/Python, server-side, OSDK integration | Not supported | 🔴 CRITICAL |
| 11 | **Ontology Auto-Mapping** | Funnel indexing: dataset row → object, declarative | Manual mappers per entity family | 🟡 LARGE |
| 12 | **Ontology Materialization** | Source + user edits combined | Not applicable (read-only) | 🟡 N/A |
| 13 | **Application Builder (Low-code)** | Workshop (60+ widgets, drag-and-drop, variables, events) | Next.js dashboard (hardcoded pages) | 🟡 LARGE |
| 14 | **Application Builder (Pro-code)** | Slate (HTML/CSS/JS), OSDK (auto-generated SDKs) | Not supported | 🔴 CRITICAL |
| 15 | **Analytics (Tabular)** | Contour (100k+ rows, visual transforms, joins) | Monthly aggregation, rankings | 🟡 LARGE |
| 16 | **Analytics (Object-driven)** | Quiver (200+ card types, time series, dashboards) | Not supported | 🟡 LARGE |
| 17 | **Analytics (Search/Explore)** | Object Explorer (keyword, filter, bulk actions) | Entity pages (partial) | 🟡 LARGE |
| 18 | **Analytics (Notebooks)** | Code Workbook (Python/R/SQL, legacy) | Not supported | 🟡 LARGE |
| 19 | **Analytics (Documents)** | Notepad (rich text, embedded widgets) | Not supported | 🟡 LARGE |
| 20 | **Analytics (Spreadsheet)** | Fusion (ontology-backed spreadsheet, writeback) | Not supported | 🟡 LARGE |
| 21 | **Geospatial** | Map (points, lines, choropleths, clusters, time series) | Not supported | 🟡 LARGE |
| 22 | **Graph Visualization** | Vertex (object relationships, events, time series) | Not supported | 🟡 LARGE |
| 23 | **Anomaly Detection** | Object Monitors (sunset), Foundry Rules, data expectations | Independent anomaly rules, drill-down | 🟢 COMPARABLE |
| 24 | **AI / LLM** | AIP Chatbot Studio, AIP Logic, AIP Assist, AIP Evals, semantic search | LLM narrates precomputed facts (insight generation) | 🔴 CRITICAL |
| 25 | **AI Observability** | Trace views, token usage, latency, log search | Basic insight generation errors logged | 🟡 LARGE |
| 26 | **Automation** | Automate (condition→effect), Autopilot, Dynamic Scheduling | Refresh orchestration, scheduled jobs | 🟡 LARGE |
| 27 | **Export** | Power BI, Tableau, ODBC/JDBC, REST APIs, Python/R SDKs, Excel, PDF | Excel only | 🟡 LARGE |
| 28 | **Observability** | Data Health, Workflow Lineage, metrics, traces, log export | Refresh status, job state tracking | 🟢 MODERATE |
| 29 | **Security** | Organizations, SAML, OAuth, RBAC, row-level, column-level, markings | Email/password auth, tenant RLS, tenant routing | 🟡 LARGE |
| 30 | **Multi-tenancy** | Full tenant isolation, organizations, user silos | Tenant access, RLS, control plane, quotas | 🟢 COMPARABLE |
| 31 | **Developer Platform** | OSDK, MCP (70+ tools), REST APIs, VS Code, CLI | None | 🔴 CRITICAL |
| 32 | **Collaboration** | Comments, branching, proposals, reviews, sharing, Marketplace | None | 🟡 LARGE |
| 33 | **Semantic Search** | Multimodal + embedding models, ontology-augmented generation | None | 🔴 CRITICAL |
| 34 | **Workflow Lineage** | Full execution graph, trace views, 7-day history | Basic refresh status | 🟡 LARGE |
| 35 | **Code Repositories** | Web IDE, Git, Python/SQL/Java transforms, CI/CD | Not supported | 🟡 LARGE |
| 36 | **Data Health** | Content validation, schema validation, alerts, PagerDuty/Slack | Not supported | 🟡 LARGE |
| 37 | **Model Catalog** | Secure connectivity to commercial LLMs, custom models, rate limiting | Single LLM provider (configurable) | 🟡 LARGE |
| 38 | **API Gateway** | REST, GraphQL, proxy endpoints for LLM providers | Internal FastAPI routes only | 🟡 LARGE |
| 39 | **Branching** | Version control for datasets, pipelines, ontology, apps | Not supported | 🟡 LARGE |
| 40 | **Event Streaming** | Kafka, Kinesis, Pub/Sub, Flink | Not supported | 🟡 LARGE |
| 41 | **Change Data Capture** | CDC syncs with changelog metadata | Deferred | 🟡 LARGE |
| 42 | **Private Link** | AWS Private Link, Azure Private Link, GCP PSC | Not supported | 🟡 LARGE |
| 43 | **Agent Worker** | On-premise agent for secure source access | Not supported | 🟡 LARGE |
| 44 | **Compute Modules** | Bring-your-own containerized runtimes | Not supported | 🟡 LARGE |
| 45 | **Schema Inference** | Auto-detect schema from CSV, JSON, Parquet | Partial (workbook profiling) | 🟢 MODERATE |
| 46 | **Data Quality** | Data expectations, health checks, unit tests | Cleaning rules, normalization | 🟢 MODERATE |
| 47 | **Incremental Sync** | Incremental pipelines, CDC, streaming | Not supported | 🟡 LARGE |
| 48 | **Data Lineage** | Complete graph: input→logic→output | Lineage graph (ingestion pipeline) | 🟢 MODERATE |
| 49 | **Time Series** | Time series properties, sync, analysis, forecasting | Monthly aggregation only | 🟡 LARGE |
| 50 | **Push Notifications** | Email, platform, PagerDuty, Slack | Not supported | 🟡 LARGE |
| 51 | **Custom Widgets** | OSDK React components, iframe widgets | Not supported | 🟡 LARGE |
| 52 | **Mobile Support** | Workshop mobile, responsive layouts | Desktop only | 🟡 LARGE |
| 53 | **Scenario Modeling** | What-if scenarios, parameter variations | Not supported | 🟡 LARGE |
| 54 | **Process Mining** | Machinery module for process analysis | Not supported | 🟡 LARGE |
| 55 | **Dynamic Scheduling** | Gantt charts, scheduling, resource allocation | Not supported | 🟡 LARGE |
| 56 | **Email/Calendar Integration** | Outlook, Gmail, calendar sync | Not supported | 🟡 LARGE |
| 57 | **Comments & Collaboration** | Comments on objects, shared lists, saved explorations | Not supported | 🟡 LARGE |
| 58 | **Audit Logging** | Comprehensive audit of all actions | Basic (refresh, export) | 🟡 LARGE |
| 59 | **Cost Attribution** | Compute, storage, LLM cost per tenant | Not supported | 🟡 LARGE |
| 60 | **API Rate Limiting** | Configurable rate limits per user/app | Not supported | 🟡 LARGE |
| 61 | **Data Retention** | Configurable policies, checkpointing | Not supported | 🟡 LARGE |
| 62 | **Data Masking** | Markings, column-level security, PII scanning | Not supported | 🟡 LARGE |
| 63 | **SSO Integration** | SAML, OAuth2, OIDC, Active Directory | Email/password only | 🟡 LARGE |
| 64 | **User Directory** | LDAP, Active Directory, Google Directory | Not supported | 🟡 LARGE |
| 65 | **Group Management** | Organizations, groups, role inheritance | Basic tenant membership | 🟡 LARGE |
| 66 | **Permission Propagation** | Inherited permissions across projects, datasets | Tenant-level RLS | 🟡 LARGE |
| 67 | **Marketplace** | Pre-built solutions, templates, sharing | Not supported | 🟡 LARGE |
| 68 | **Solution Designer** | Architectural diagramming tool | Not supported | 🟡 LARGE |
| 69 | **Training Application** | In-platform courses, certifications | Not supported | 🟡 LARGE |
| 70 | **AIP Assist** | In-platform LLM helper for navigation | Not supported | 🟡 LARGE |
| 71 | **AIP Evals** | LLM output testing framework | Not supported | 🔴 CRITICAL |
| 72 | **LLM Proxy Endpoints** | Proxy for OpenAI, Anthropic, etc. with rate limiting | Not supported | 🟡 LARGE |
| 73 | **Zero Data Retention** | Configurable ZDR for LLM calls | Not supported | 🟡 LARGE |
| 74 | **Context Engineering** | Retrieval context, tool definitions, grounding | Not supported | 🔴 CRITICAL |
| 75 | **Vector Database** | Embedding storage, similarity search | Not supported | 🔴 CRITICAL |
| 76 | **Multi-modal AI** | Image, document, audio processing | Not supported | 🟡 LARGE |
| 77 | **Agent Framework** | Autonomous agent execution, tool calling | Not supported | 🔴 CRITICAL |
| 78 | **MCP Server** | Model Context Protocol for external AI agents | Not supported | 🔴 CRITICAL |
| 79 | **Palantir MCP** | 70+ tools for ontology building | Not supported | 🔴 CRITICAL |
| 80 | **OpenAPI Spec** | Auto-generated from platform APIs | Not supported | 🟡 LARGE |
| 81 | **SDK Generation** | TypeScript, Python, Java from ontology | Not supported | 🔴 CRITICAL |
| 82 | **Webhook System** | Inbound and outbound webhooks | Not supported | 🟡 LARGE |
| 83 | **Event Streaming API** | Real-time subscriptions to object changes | Not supported | 🟡 LARGE |
| 84 | **Data Connect API** | ODBC/JDBC for external BI tools | Not supported | 🟡 LARGE |

---

## Architecture Incompatibilities

Canopy has **deliberate** design choices that are not gaps but differences. These should be preserved in any roadmap:

### 1. Read-Only to Source

Canopy's rule #1: "The application never writes back to the source system."
Palantir's Ontology Actions do write back. This is a product choice, not a technical limitation. Any roadmap should preserve this unless the product strategy explicitly changes.

**Implication:** Phases for Action Types, writeback pipelines, and user-editable objects are out of scope unless the user explicitly requests them.

### 2. Deterministic-First Analytics

Canopy's rule #2: "Deterministic analytics decide. The LLM narrates."
Palantir's AI can directly influence data through AIP Logic and chatbot actions. Canopy's AI is limited to generating text summaries from precomputed facts.

**Implication:** Any AI phase must preserve the deterministic boundary. AI can suggest, narrate, and assist, but metrics must always be computed by code first.

### 3. Snapshot-Scoped Consistency

Canopy's rule #3: "Dashboard, export, and AI must use the same snapshot basis."
Palantir allows real-time streaming and near-instant updates. Canopy's refresh model is batch-based with snapshot isolation.

**Implication:** Moving to real-time is a major architectural change. The roadmap should keep batch/analytical as the default, with streaming as a future optional layer.

### 4. HR Domain Focus

Palantir is general-purpose. Canopy is HR spend intelligence.

**Implication:** The Ontology Builder phase (Phase 8) should be scoped to domain-specific types, not attempt to become a general-purpose ontology platform like Palantir's. Focus on HR, finance, and operations object types.

### 5. Single-Codebase Monolith

Palantir runs hundreds of services. Canopy is a modular monolith.

**Implication:** The roadmap should assume the monolith structure persists. Microservices should only be extracted when a module clearly needs independent scaling.

### 6. No Versioned Runtime Code

Canopy's naming rule: phase labels like `v2`, `v3` are planning markers only, never runtime prefixes.

**Implication:** The roadmap should never propose `v7_api`, `v8_ontology`, etc. Use domain names: `connector_framework`, `dynamic_ontology`, `analytics_engine`.

---

## Key Takeaways

### Top 5 Critical Gaps

1. **Source Connectivity:** Canopy has 3 source types; Palantir has 200+. This is the foundational gap. Without universal connectors, Canopy cannot ingest the breadth of data needed for a true data operating system.
2. **Dynamic Ontology:** Canopy's 6 hardcoded types cannot grow with user needs. A dynamic ontology builder is the single most important feature after connectors.
3. **AI Platform:** Canopy's AI is a one-way summarizer. Palantir's AI is a platform: chatbots, semantic search, context engineering, evals. This is the biggest competitive gap.
4. **Developer Platform:** Canopy has no external API, no SDK, no MCP. This prevents external developers and AI agents from building on top of Canopy.
5. **Application Builder:** Canopy's dashboard is hardcoded. A composable widget-based builder would enable users to create their own analytics surfaces without code changes.

### Top 3 Moderate Gaps (Worth Addressing Soon)

1. **Analytics Engine:** Canopy's monthly aggregation is limited. A generic analytics engine with time series, multi-dimensional aggregation, and statistical functions would unlock deeper analysis.
2. **Automation:** Canopy has refresh orchestration but no general automation. Condition-based triggers, alerts, and notifications would make it operational rather than just analytical.
3. **Observability:** Data Health, Workflow Lineage, and trace views are needed for production-grade reliability.

### Top 3 Comparable Strengths

1. **Multi-tenancy:** Canopy's v5 tenant context, RLS, and control plane are comparable to Palantir's tenant isolation.
2. **Anomaly Detection:** Canopy's anomaly rules with drill-down are comparable in depth to Palantir's rule-based detection.
3. **Data Quality:** Canopy's cleaning engine, normalization pipeline, and dataset versioning are comparable to Palantir's basic data quality features.

### Bottom Line

Canopy is 6-12 major architectural phases away from being a Palantir-like platform. The most critical path is:

**Connectors → Ontology → Analytics → AI → Developer Platform**

Each phase builds on the previous. Without connectors, the ontology cannot grow. Without a dynamic ontology, analytics cannot be generic. Without generic analytics, AI cannot be grounded in facts. Without a developer platform, Canopy cannot become an ecosystem.

---

## Document Notes

- **Source:** Palantir Foundry documentation (https://www.palantir.com/docs/foundry/)
- **Canopy Source:** `ARCHITECTURE.md`, `QUICKSTART.md`, `doc/codebase-map.md`
- **Date:** 2026-06-09
- **Status:** Comparison complete, ready for roadmap alignment

---

[Next: Canopy Enhancement Roadmap](canopy-enhancement-roadmap.md)
