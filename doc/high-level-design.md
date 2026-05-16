# High-Level Design: Executive HR Spend Intelligence Platform

> Historical note:
> This document describes the approved v1 design baseline.
> V1 is now complete. Keep this file as the architectural design record for v1,
> not as an active “next step” planning document.

## Overview

This system is a read-only executive intelligence platform for HR-related spend. It consolidates internal operational data, maps it into business objects, computes monthly spend views, detects anomalies, and presents both dashboard visuals and AI-generated recommendations.

The architecture follows the product direction defined in the proposal:

- Semantic layer: unify raw source data into business objects
- Kinetic layer: expose read-only insight and drill-down interfaces
- Dynamic layer: support daily synchronization and manual refresh

V1 was intentionally optimized for:

- Executive summary consumption
- Department-level anomaly detection
- Controlled drill-down into supporting evidence
- Clear separation between source ingestion, business modeling, analytics, AI explanation, and user-facing delivery

## System Context

### External Dependencies

- Internal database as the only v1 source system
- LLM provider for natural-language insight generation
- Email/password authentication store managed by the application
- Excel export library

### Main Runtime Components

- Next.js frontend
- FastAPI backend
- Application database for normalized ontology data, derived analytics, user auth, and sync metadata
- Background job runner for scheduled sync and AI summary generation

## Architectural Style

The recommended architecture is a modular monolith with asynchronous background jobs.

Why this shape fit v1:

- Easier to build and maintain than early microservices
- Keeps ontology, analytics, and AI logic in one coherent backend
- Supports later extraction of sync, analytics, or AI pipelines if scale requires it
- Reduces operational complexity while requirements are still settling

## Major Modules

## 1. Web Application Module

### Responsibility

- Provide the executive dashboard UI
- Handle login and session-based user flows
- Render summary metrics, trend charts, anomaly cards, and drill-down pages
- Trigger Excel export and manual refresh actions

### Main Responsibilities In Practice

- Executive summary landing page
- Department comparison views
- Monthly trend charts
- Claim drill-down tables
- Refresh status and sync timestamp display

### Interfaces

- Calls backend APIs for dashboard data
- Calls backend API to trigger manual refresh
- Calls backend API to request Excel export

## 2. API Gateway / Application API Module

### Responsibility

- Expose typed HTTP APIs to the frontend
- Validate request parameters and authentication
- Route queries to the right domain services
- Keep frontend contracts stable and explicit

### Main API Areas

- Authentication
- Executive summary
- Department analytics
- Trend data
- Anomaly views
- Drill-down queries
- Export generation
- Refresh control and refresh status

### Design Intent

This layer should stay thin. It coordinates requests but should not hold analytics or ontology transformation logic directly.

## 3. Identity And Access Module

### Responsibility

- Manage simple email/password login for v1
- Issue and validate authenticated sessions or tokens
- Store minimal user identity and access metadata

### V1 Boundary

- Simple authentication only
- No advanced enterprise authorization
- No row-level access segmentation

### Future Path

This module is intentionally isolated so later SSO or role-based access control can replace or extend it without rewriting analytics logic.

## 4. Source Sync Module

### Responsibility

- Read source data from the internal database
- Pull the required HR and spend entities on a schedule
- Support manual refresh initiation
- Track sync status, timestamps, and errors

### Data Covered In V1

- Employee-related source records
- Department source records
- Cost center source records where available
- Claim expense source records
- Payroll expense source records
- Budget code or spend classification records

### Sync Behavior

- Daily scheduled sync
- Manual refresh trigger from UI
- Refresh metadata visible to user

### Design Intent

This module should be the only place that knows raw source schemas in detail. The rest of the system should consume normalized business objects, not raw source tables.

## 5. Semantic / Ontology Mapping Module

### Responsibility

- Convert raw source rows into normalized business objects
- Resolve source-specific naming and structures into application-level ontology
- Preserve traceability between ontology objects and source records

### Core V1 Objects

- Department
- Employee
- CostCenter
- ExpenseClaim
- PayrollExpense
- BudgetCode

### Core Responsibilities

- Build normalized employee identity from multiple HR source structures
- Keep claim expense and payroll expense as separate object families
- Connect department, employee, cost center, and expense relationships
- Preserve source lineage for audit and drill-down

### Important Design Decision

Do not collapse claim and payroll into one fake expense table too early.

Reason:

- Claim records behave like discrete business transactions
- Payroll behaves more like derived or summarized cost data in the current domain
- Keeping them separate avoids wrong assumptions and supports cleaner executive explanation

## 6. Analytics Aggregation Module

### Responsibility

- Build the monthly views used by dashboards and exports
- Aggregate spend by department, month, employee, and claim type
- Provide efficient query-ready data structures for the product

### Main Outputs

- Total payroll spend by month
- Total claim spend by month
- Department total spend rankings
- Department month-over-month deltas
- Claim type contribution breakdowns
- Employee-level contribution summaries

### Design Intent

This module should precompute the expensive business views needed for fast executive dashboards rather than repeatedly computing them directly from raw source data.

## 7. Anomaly Detection Module

### Responsibility

- Detect unusual department spend changes
- Detect unusually high department claim expense
- Produce explainable anomaly results for UI and AI summary generation

### V1 Detection Focus

- Month-over-month department spend spikes
- Department claim expense anomalies

### Output Shape

An anomaly result should include:

- Target entity, usually a department
- Time period
- Measured change
- Likely contributing components, such as payroll vs claims
- Supporting drill-down keys

### Design Intent

This module should produce deterministic, explainable anomaly facts first. The LLM should explain those facts, not invent them.

## 8. Insight Generation Module

### Responsibility

- Turn computed metrics and anomaly facts into executive-facing natural-language summaries
- Generate read-only recommendations
- Keep AI output grounded in system-generated data

### Input

- Executive summary metrics
- Trend metrics
- Ranked departments
- Anomaly outputs
- Drill-down support data

### Output

- AI-written explanation of what changed
- AI-written explanation of likely drivers
- Read-only recommendations for what the executive should review next

### Guardrail

This module must not trigger actions or write back to operational systems.

### Design Intent

LLM generation should happen after the platform has already computed the facts. The model is a summarizer and interpreter, not the primary analytics engine.

## 9. Reporting And Export Module

### Responsibility

- Generate Excel exports aligned with visible dashboard data
- Package executive summary and breakdown data into downloadable output

### V1 Scope

- Excel export only
- Export structure should mirror the dashboard’s summary and drill-down logic

### Design Intent

Exports should come from the same derived data views used by the product UI to avoid reconciliation gaps.

## 10. Refresh Orchestration And Job Module

### Responsibility

- Run daily sync jobs
- Run manual refresh jobs
- Trigger downstream normalization, aggregation, anomaly detection, and insight generation
- Track job state and failures

### Job Flow

- Sync source data
- Normalize into ontology
- Recompute analytics views
- Recompute anomalies
- Regenerate executive summaries
- Mark refresh complete

### Design Intent

This module separates long-running work from synchronous user requests, keeping the UI responsive while preserving consistent refresh sequencing.

## 11. Application Data Store Module

### Responsibility

- Store normalized ontology objects
- Store derived monthly aggregates
- Store anomaly records
- Store cached AI summaries
- Store user auth and refresh metadata

### Logical Data Zones

- Source snapshot or staging zone
- Ontology zone
- Analytics zone
- Insight cache zone
- Application metadata zone

### Design Intent

The data store must support both traceability and query speed. V1 should favor explicit derived tables or materialized views over clever but opaque runtime query chains.

## Data Flow

## 1. Ingestion Flow

- Source Sync Module reads from the internal database
- Raw source records are written to staging or source snapshot storage
- Semantic / Ontology Mapping Module transforms them into normalized business objects

## 2. Analytics Flow

- Analytics Aggregation Module computes monthly spend views
- Anomaly Detection Module evaluates department-level change signals
- Results are persisted for API access and export use

## 3. Insight Flow

- Insight Generation Module receives precomputed facts
- It generates grounded executive summaries and recommendations
- The summaries are stored for dashboard display and export inclusion

## 4. User Interaction Flow

- User logs in through the Web Application Module
- Frontend requests summary and drill-down data from the API
- API reads prepared analytics and insight results from the application store
- User can trigger export or manual refresh

## 5. Manual Refresh Flow

- User invokes refresh from the UI
- API submits a refresh job
- Refresh Orchestration runs sync -> normalize -> aggregate -> detect -> summarize
- Frontend polls or reloads refresh status

## External Interfaces

## Frontend To Backend

Main API interface groups:

- `auth`
- `summary`
- `departments`
- `trends`
- `anomalies`
- `drilldown`
- `exports`
- `refresh`

The exact route structure belongs in detailed design, but the high-level contract should remain organized around business capabilities, not raw tables.

## Backend To Source System

- Read-only internal database connection

This interface should be isolated behind the Source Sync Module so the rest of the application does not depend on source schema churn.

## Backend To LLM Provider

- Summarization request interface

The backend should send structured, precomputed facts and receive narrative output, rather than sending raw source data with open-ended prompts.

## Cross-Cutting Concerns

## Auditability

- Every executive metric should be traceable back to source records or derived aggregates
- AI summary output should be tied to the exact metrics and anomaly set used to generate it

## Performance

- Dashboard endpoints should read precomputed monthly views where possible
- Heavy sync and summarization work should be asynchronous

## Reliability

- Manual refresh and daily sync need job-state tracking
- Partial refresh states should not silently overwrite known-good dashboard data

## Security

- Use standard password hashing and secure session or token handling
- Keep source access read-only
- Prevent AI module from being used as a write path

## Observability

- Record sync duration, failure reasons, and last successful refresh time
- Record anomaly generation timing and AI summary generation errors

## Consistency

- Export results and dashboard results must come from the same derived data basis
- AI summaries must align with the same snapshot the user is seeing

## Main Design Tradeoffs

## 1. Separate Claim And Payroll Expenses

Chosen approach:

- Keep them as separate business object families, then aggregate upward

Tradeoff:

- Slightly more modeling effort now
- Much safer semantics and cleaner future evolution

## 2. Derived Views Over Live Querying

Chosen approach:

- Precompute monthly analytics and anomaly data

Tradeoff:

- More refresh-pipeline work
- Better dashboard speed, easier exports, clearer audit path

## 3. Modular Monolith Over Microservices

Chosen approach:

- Single backend application with strong internal boundaries

Tradeoff:

- Less deployment flexibility early
- Much lower complexity and faster delivery for v1

## 4. AI As Explanation Layer, Not Decision Engine

Chosen approach:

- Compute facts deterministically, then summarize with AI

Tradeoff:

- Requires more backend analytics logic up front
- Greatly improves trust, explainability, and maintainability

## 5. Simple Auth First

Chosen approach:

- Email/password only in v1

Tradeoff:

- Not enterprise-ready
- Keeps v1 focused on insight delivery rather than access-model design

## Deferred Items For Detailed Design

Historical note:
These items were deferred at the high-level design stage and have since been
addressed or superseded by implementation and later docs.

- Exact database schema for normalized ontology and aggregates
- Exact API route definitions and payload schemas
- Exact anomaly formulas and threshold tuning
- Exact LLM prompt structure and response contract
- Refresh job scheduling technology and worker model
- Excel workbook sheet layout
- Session strategy and auth implementation details
- Caching strategy
- Error-state UX and refresh progress UX
- Future Excel import architecture
- Future role-based access design
- Future near-real-time sync architecture

## Status

This document no longer defines the next document to write.

For current-state implementation and repo status, use:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md)
- [`doc/codebase-map.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/codebase-map.md)
- [`doc/v2-plan.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/v2-plan.md)
