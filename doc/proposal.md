# Proposal: Executive HR Spend Intelligence Platform

## Goal

Build a Palantir-like web application for C-level users to understand HR-related spend, detect unusual changes, and make better decisions from consolidated operational data.

The v1 system is insight-first. It gathers data, models it into a usable ontology, visualizes it, detects anomalies, and produces read-only AI-generated recommendations. It does not trigger operational actions.

## Background

The initial domain is human resources with finance and business intelligence usage, focused on spend visibility and executive insight.

The main user is a C-level stakeholder who needs to answer:

- Which departments are spending the most?
- Which departments show unusual month-over-month increases?
- Why did spending change?
- Which employees, claim types, or monthly movements are driving the change?

The current source of truth is an internal database. Excel import is a later enhancement, not part of the first production slice.

## Scope

V1 includes:

- A web application with executive dashboard views
- Simple login with email and password
- Daily scheduled sync from the internal database
- Manual refresh capability
- Monthly spend analytics
- Drill-down from executive summary into department, employee, claim type, and month detail
- AI-generated natural-language insight summaries and read-only recommendations
- Excel export of summary and breakdown data

## Non-goals

V1 does not include:

- Write-back into HerdHR or any operational source system
- Triggering approvals or actions
- Forecasting or predictive planning
- Chat assistant workflows
- Row-level or advanced enterprise access control
- Real-time or near-real-time synchronization
- Multi-source import beyond the internal database
- Excel file import in the initial version

## Target Users

- Primary user: C-level executive

Secondary users may be added later, but the first product slice is optimized for executive visibility and decision support.

## Product Direction

The application should resemble a Palantir-style operational intelligence system, but focused on HR and spend insight:

- Semantic layer: structure raw HR and spend data into meaningful business objects
- Kinetic layer: for v1, provide read-only recommendations only
- Dynamic layer: daily synchronization plus manual refresh, with near-real-time deferred to later versions

## Inputs

Current v1 inputs:

- Internal database

Future inputs, out of scope for v1:

- Excel file import

## Outputs

V1 outputs:

- Executive web dashboard
- Department-level and trend visualizations
- AI-generated natural-language executive summary
- Excel export containing summary and breakdown data

## Ontology

### Core V1 Objects

- Department
- Employee
- CostCenter
- ExpenseClaim
- PayrollExpense
- BudgetCode

### Notes On Source Mapping

The ontology is informed by the current HerdHR data model and should avoid forcing generic labels that do not match the real schema.

Recommended source mapping:

- `Department` maps to department entities
- `Employee` maps to the effective employee identity composed from user, profile, and job data
- `CostCenter` maps to cost center assignment data
- `ExpenseClaim` maps to claim application records
- `PayrollExpense` maps to payroll detail spend records
- `BudgetCode` maps to payroll/pay-item coding used to classify expense types

### Core Relationships

Required v1 relationships:

- Employee belongs to Department
- Employee may be assigned to CostCenter
- ExpenseClaim belongs to Employee
- ExpenseClaim belongs to a claim type or budget code
- PayrollExpense is attributable to Department
- PayrollExpense may be attributable to CostCenter
- Department aggregates PayrollExpense and ExpenseClaim

### Important Boundary

There is no trustworthy first-class generic `Expense` object in the current source model. V1 should model claim expense and payroll expense separately, then aggregate them into executive spend views.

## Functional Requirements

### Authentication

- Users can log in with email and password
- V1 uses simple authentication only

### Data Synchronization

- The system syncs data from the internal database on a daily schedule
- The system provides a manual refresh function
- The system records last refresh time for the user

### Executive Summary Dashboard

The landing page must focus on overall executive summary and include:

- Total payroll spend for the current month
- Total claim spend for the current month
- Top departments by spend
- Departments with unusual month-over-month increase
- AI-written summary of what changed and why
- Trend chart covering the last 6 to 12 months

### Drill-down Analysis

The user can drill from executive summary into:

- Department
- Employee
- Claim type
- Month

Recommended transaction granularity for v1:

- Claims: individual claim application detail
- Payroll: monthly summarized departmental totals first, with optional employee-level summary later

This keeps payroll insight useful without forcing weak transaction semantics too early.

### Anomaly Detection

V1 anomaly detection must identify:

- Departments whose total spend spikes month-over-month
- Departments with unusually high claim expense

The anomaly output should support executive review by showing:

- Which department changed
- Size of change
- Main drivers of change where derivable from data
- Drill-down path into employees, claim types, and months

### AI Insight Generation

The backend should generate natural-language insight summaries for executives.

V1 AI behavior:

- Read-only recommendation only
- No action execution
- No system write-back
- No autonomous approvals

The AI summary should explain:

- What changed
- Which departments changed most
- Whether payroll or claims drove the change
- Which claim types or employee clusters likely contributed

### Reporting

- Users can export an Excel report
- The export should align with the visible summary and breakdown data used in the dashboard

## Recommended Technical Stack

### Frontend

- Next.js
- TypeScript

### Backend

Recommended backend:

- FastAPI with Python

Reason for recommendation:

- Strongest ecosystem fit for AI, analytics, and data-processing workloads
- High performance with typed API development
- Good maintainability through explicit schema models and validation
- Clear separation between product UI and ontology/data services

## Non-functional Requirements

- Maintainable typed API contracts
- Clear object model for future ontology expansion
- Good performance for executive dashboards over monthly aggregated data
- Support for later AI and data-source expansion without rewriting core architecture
- Clear auditability of how dashboard totals and summaries are derived

## Acceptance Criteria

V1 is complete when all of the following are true:

- A C-level user can log in successfully
- The user can open the dashboard and see correct monthly payroll and claim trends
- The system detects abnormal department spikes and explains likely drivers
- The user can drill into department, employee, claim type, and month
- The user can export an Excel report containing the relevant summary and breakdown

## Risks And Later Decisions

- Payroll source data may not behave like clean line-by-line executive transaction data, so v1 should avoid overcommitting to deep payroll transaction detail
- The source model may have weak or incomplete cost center coverage in some tenants
- Budget tables do not yet exist, so v1 should not present false “budget overrun” claims
- Access control is intentionally simple in v1 and will need redesign later
- Near-real-time synchronization is deferred and may require architectural changes later

## Open Questions Resolved

- Domain: human resource spend intelligence
- Primary user: C-level executive
- Primary decision: identify overspending departments, understand why, and review what to do next
- Initial input source: internal database
- Future import: Excel later
- Initial ontology direction: Department, Employee, CostCenter, ExpenseClaim, PayrollExpense, BudgetCode
- Expense coverage: both payroll and claim expense
- Budget model: no real budget table in v1
- Initial anomaly focus: month-over-month department spend spikes and unusually high department claim expense
- Recommended action pattern: drill into department, employee, claim type, and month breakdown
- Delivery target: web app plus downloadable Excel report
- Frontend stack: Next.js with TypeScript
- Backend stack: FastAPI with Python
- AI scope: natural-language read-only recommendations
- Authentication: simple email and password
- Date grain: monthly with drill-down
- Refresh model: daily scheduled sync plus manual refresh
- V1 posture: gather data, show insight, no triggered actions
