# V2 Detailed Design: Analytics Shell And Dashboard UX Refresh

## Purpose

This document expands the agreed v2 direction into an implementation-ready
design for the analytics shell and dashboard UX refresh.

It is the v2 counterpart to the historical v1 detailed design. It does not
replace [`doc/detailed-design.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/detailed-design.md).

This document follows:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md)
- [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md)
- [`doc/v2-plan.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/v2-plan.md)
- [`doc/v2-uiux-design.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/v2-uiux-design.md)

If these documents conflict, `ARCHITECTURE.md` remains the source of truth for
architecture and `DESIGN.md` remains the source of truth for visual language.

## V2 scope

V2 is a UX-depth phase, not a system rewrite.

V2 delivers:

- shared analytics sidebar shell
- tighter dashboard command view
- stronger page-level hierarchy for `Anomalies`, `Departments`, `Reports`, and
  `Profile`
- explicit drill-down and time-range carry-over behavior
- responsive sidebar adaptation without changing the desktop-first information
  architecture

V2 does not deliver:

- new anomaly workflow state
- scheduled exports
- major data-model redesign
- multi-tenant runtime changes
- mobile-first re-architecture

## Main design goals

V2 must improve:

- executive scan speed
- workspace efficiency on desktop
- consistency of navigation and page framing
- testability through sharper frontend module boundaries

V2 must preserve:

- snapshot consistency
- deterministic analytics before AI narration
- existing backend domain boundaries
- narrow API-to-service-to-repository layering

## Module layout

V2 should be implemented through these module groups.

### Frontend modules

- `analytics-shell`
- `navigation-state`
- `dashboard-v2`
- `anomalies-v2`
- `departments-v2`
- `department-detail-v2`
- `reports-v2`
- `profile-v2`
- `frontend-api-adapters-v2`
- `frontend-testing-v2`

### Backend support modules

- `analytics-read-api-v2`
- `export-history-api-v2`
- `refresh-status-api-v2`

These backend modules are support changes only. They exist to serve the new
frontend shell and page contracts without changing the product's core data flow.

## Frontend architecture

## Shared analytics shell

### Responsibilities

The shell owns:

- sidebar navigation
- sidebar collapse state
- responsive drawer behavior
- lightweight page header frame
- breadcrumb placement rules
- bottom utility zone
- content-area sizing and spacing

The shell does not own:

- page-specific business data
- chart shaping
- anomaly ranking rules
- export generation logic

### Proposed component split

```text
apps/frontend/src/components/analytics-shell/
  analytics-shell.tsx
  analytics-sidebar.tsx
  analytics-sidebar-item.tsx
  analytics-sidebar-brand.tsx
  analytics-sidebar-utilities.tsx
  analytics-header.tsx
  analytics-breadcrumb.tsx
  analytics-drawer.tsx
  analytics-layout-context.tsx
```

### Internal responsibilities

- `analytics-shell.tsx`
  - compose sidebar, header, content frame
  - expose shell slots to pages
- `analytics-layout-context.tsx`
  - hold collapse and drawer state only
  - no page data
- `analytics-header.tsx`
  - render title, optional context text, action slot
- `analytics-breadcrumb.tsx`
  - render nested-page breadcrumb only
- `analytics-sidebar.tsx`
  - render stable primary nav cluster plus utility cluster

### Shell state rules

Shell state includes only:

- `sidebar_expanded: boolean`
- `mobile_drawer_open: boolean`

This state should persist per browser where simple to do so.

Shell state must not include:

- selected time range
- page filters
- anomaly severity filter
- department search text

Those belong to page-level modules.

## Navigation and route-state module

### Responsibilities

This module standardizes how pages read and write:

- current time range
- department filter carry-over
- anomaly drill-down context
- breadcrumb metadata

### Proposed split

```text
apps/frontend/src/lib/navigation/
  time-range.ts
  route-state.ts
  dashboard-links.ts
  anomaly-links.ts
  department-links.ts
```

### Key structures

```ts
type TimeRangeKey = 'this_month' | 'last_3_months' | 'last_12_months'

type DepartmentDrillContext = {
  departmentId: string
  timeRange: TimeRangeKey
  source?: 'dashboard_attention' | 'dashboard_ranking' | 'anomalies'
  anomalyId?: string
}

type AnomalyPageContext = {
  timeRange: TimeRangeKey
  departmentId?: string
  severity?: 'high' | 'medium' | 'low'
}
```

### Rules

- route state must remain serializable
- pages read route state through one adapter layer
- link builders create URLs; page components do not hand-build query strings
- time-range defaults live in one shared module

## Dashboard v2 module

### Responsibilities

`dashboard-v2` owns:

- command-view layout
- attention panel composition
- summary-card block composition
- AI summary panel composition
- read-only trend panel composition
- top-5 department preview composition

### Proposed split

```text
apps/frontend/src/components/dashboard-v2/
  dashboard-page.tsx
  dashboard-summary-grid.tsx
  dashboard-attention-panel.tsx
  dashboard-attention-item.tsx
  dashboard-ai-summary-panel.tsx
  dashboard-trend-panel.tsx
  dashboard-department-preview.tsx
  dashboard-mappers.ts
```

### Data contract

The dashboard page should receive one composed read model from the adapter
layer.

```ts
type DashboardCommandView = {
  snapshotId: string
  snapshotLabel: string
  timeRange: TimeRangeKey
  summaryCards: {
    totalSpend: MetricCard
    payrollSpend: MetricCard
    claimsSpend: MetricCard
    attentionCount: MetricCard
  }
  topAttentionItems: AttentionListItem[]
  aiSummary: SummaryBrief
  trendSeries: TrendSeries[]
  topDepartments: DepartmentPreviewItem[]
}
```

### Interaction rules

- clicking `Attention Count` routes to `Anomalies` with current time range
- clicking a top attention item routes to department detail with context
- clicking a department preview row routes directly to department detail
- `View all anomalies` routes to anomalies page
- `View all departments` routes to departments page
- trend panel stays non-interactive

### Control flow

1. page reads current time range from route-state module
2. page fetches dashboard read model through adapter
3. mapper normalizes response into `DashboardCommandView`
4. page passes plain props into presentational sections
5. top-right header actions invoke export or refresh side effects through
   dedicated adapters only

## Anomalies v2 module

### Responsibilities

`anomalies-v2` owns:

- severity-grouped triage list
- time-range and severity filter controls
- collapsed/expanded section behavior
- compact anomaly-row presentation

### Proposed split

```text
apps/frontend/src/components/anomalies-v2/
  anomalies-page.tsx
  anomalies-filter-bar.tsx
  anomalies-group.tsx
  anomaly-row.tsx
  anomaly-mappers.ts
```

### Data contract

```ts
type AnomalyListView = {
  snapshotId: string
  timeRange: TimeRangeKey
  groups: {
    severity: 'high' | 'medium' | 'low'
    count: number
    items: AnomalyListItem[]
  }[]
}
```

### Interaction rules

- `High` is expanded by default
- `Medium` and `Low` start collapsed
- row click routes to department detail
- no mark-reviewed or dismiss state mutation exists in v2

### Control flow

1. page reads time range and optional department prefilter
2. adapter requests filtered anomaly list
3. mapper groups by severity
4. page renders grouped sections with local expand/collapse UI state

## Departments index v2 module

### Responsibilities

`departments-v2` owns:

- ranked departments index
- search, attention filter, time-range, and primary sort controls
- hybrid ranked-row rendering

### Proposed split

```text
apps/frontend/src/components/departments-v2/
  departments-page.tsx
  departments-filter-bar.tsx
  department-ranked-row.tsx
  department-list-mappers.ts
```

### Data contract

```ts
type DepartmentRankingView = {
  snapshotId: string
  timeRange: TimeRangeKey
  activeSort: 'attention' | 'total_spend' | 'change_percent'
  items: DepartmentRankingItem[]
}
```

### Rules

- default sort is `attention`
- only one active sort is exposed in UI
- no summary strip
- one selected time range only
- row click routes to department detail

## Department detail v2 module

### Responsibilities

`department-detail-v2` owns:

- summary header
- visible time-range control
- breadcrumb rendering
- trend hero panel
- smaller department AI summary
- equal split contributor panels
- `View related anomalies` CTA

### Proposed split

```text
apps/frontend/src/components/department-detail-v2/
  department-detail-page.tsx
  department-detail-header.tsx
  department-trend-panel.tsx
  department-ai-summary.tsx
  department-contributors-split.tsx
  department-employee-panel.tsx
  department-claim-type-panel.tsx
  department-detail-mappers.ts
```

### Data contract

```ts
type DepartmentDetailView = {
  snapshotId: string
  department: {
    id: string
    name: string
    attentionState: string
  }
  timeRange: TimeRangeKey
  summary: {
    totalSpend: number
    changePercent: number
  }
  trend: TrendSeries[]
  aiSummary: SummaryBrief
  topEmployees: ContributorItem[]
  topClaimTypes: ContributorItem[]
}
```

### Interaction rules

- page is long-scroll, not tabbed
- time-range changes refetch whole page consistently
- `View related anomalies` routes to `Anomalies` with department and time range
  pre-applied
- no detailed transaction table in v2

## Reports v2 module

### Responsibilities

`reports-v2` owns:

- export preset workspace
- recent export history
- inline failed/exporting/completed status presentation
- `Run again` action

### Proposed split

```text
apps/frontend/src/components/reports-v2/
  reports-page.tsx
  report-preset-grid.tsx
  report-history-list.tsx
  report-history-row.tsx
  report-mappers.ts
```

### Data contract

```ts
type ReportsWorkspaceView = {
  presets: ExportPreset[]
  recentExports: ExportHistoryItem[]
}

type ExportHistoryItem = {
  id: string
  presetName: 'Executive Summary' | 'Department Spend' | 'Anomaly Review'
  status: 'queued' | 'running' | 'completed' | 'failed'
  createdAt: string
  timeRange: TimeRangeKey
  snapshotTimestamp: string
  errorSummary?: string
}
```

### Interaction rules

- no summary strip
- presets shown first
- recent history after presets
- completed rows expose `Download` and `Run again`
- failed rows expose user-facing summary plus optional details
- no scheduled exports in v2

## Profile v2 module

### Responsibilities

`profile-v2` owns a lightweight in-shell account page only.

It should include:

- account identity summary
- basic session or account metadata if needed

It should not introduce a settings surface unless a real product requirement is
added later.

## Frontend API adapter boundary

### Responsibilities

Adapters must absorb transport details for the new pages and shell actions.

### Proposed split

```text
apps/frontend/src/lib/api/
  analytics-shell.ts
  dashboard-v2.ts
  anomalies-v2.ts
  departments-v2.ts
  reports-v2.ts
  refresh-v2.ts
  exports-v2.ts
```

### Rules

- page components never consume raw backend JSON
- adapters validate and map responses
- time-range params are normalized before request dispatch
- UI labels such as `Attention Count` remain UI terms; transport contracts may
  still use `anomaly_count` or a neutral backend field name

## Backend support design

## API route groups

V2 should prefer extending existing groups rather than introducing unrelated
top-level groups.

Recommended routes or route revisions:

- `GET /api/dashboard/command-view`
- `GET /api/anomalies`
- `GET /api/departments`
- `GET /api/departments/{department_id}/detail-view`
- `GET /api/reports/history`
- `POST /api/reports/exports`
- `POST /api/reports/exports/{export_id}/rerun`
- `GET /api/refresh/current`

If existing v1 routes already cover these needs, keep route count smaller and
adapt response shapes instead of duplicating surfaces.

## Backend service changes

### Required service responsibilities

- `DashboardSummaryService`
  - add v2 command-view assembler
- `AnomalyService`
  - add grouped list read model support
- `DepartmentAnalysisService`
  - add department detail read model assembler
- `ExportService`
  - add export history read model and rerun flow
- `RefreshService`
  - add compact refresh-status view for header drawer

### Service rules

- services return typed read models
- grouping, ranking, and derived display facts belong in services or dedicated
  mapper modules, not in route handlers
- routes stay thin

## Refresh and export operational controls

### Refresh control

The dashboard header refresh control is a richer split control, but it still
maps to the existing asynchronous refresh pipeline.

Required data:

- current refresh status
- last successful snapshot label
- last run timestamp
- last error summary where relevant

Frontend drawer state is local UI state. Backend remains responsible only for
supplying refresh facts.

### Export control

The dashboard header export action is a quick preset trigger.

Required presets:

- `Executive Summary`
- `Department Spend`
- `Anomaly Review`

Header export behavior:

- trigger export request quickly
- do not redirect to reports by default
- keep richer export-history behavior in `Reports`

## Error handling

## Frontend state model

Each page module must explicitly distinguish:

- loading
- empty
- stale but usable
- failed refresh background state
- fatal page load failure

### Page-specific rules

- shell should remain mounted on page data failure
- header operational controls should fail independently where possible
- export-row failure details should not crash reports page
- collapsed sidebar state should not be reset by page fetch failures

## Backend error rules

- invalid time-range or filter payloads return validation errors
- export rerun on invalid export id returns a client-safe error
- grouped anomaly fetch failure returns a stable API error envelope
- refresh failures do not clear current snapshot visibility

## Testing strategy

V2 must preserve the architecture rule that most logic stays testable without
full-app boot.

## Frontend unit tests

Must cover:

- sidebar collapse and drawer-state behavior
- header rendering with and without breadcrumb
- route-state builders and parsers
- dashboard command-view mappers
- anomalies grouping mappers
- departments ranking mappers
- reports history row mappers
- department detail contributor split render behavior

Preferred seam order:

1. pure route-state and mapper tests
2. presentational component tests with plain props
3. container tests with mocked adapters

## Frontend integration tests

Must cover:

- dashboard default load with sidebar shell
- attention count click to anomalies with time range carried over
- top attention item click to department detail with context carried over
- `View related anomalies` CTA from department detail
- reports preset trigger and history update behavior
- responsive drawer open/close behavior at smaller breakpoints

## Backend unit tests

Must cover:

- v2 dashboard command-view assembler
- anomaly list grouping logic
- department detail read-model assembler
- export history summary mapper
- refresh-status compact view mapper

## Backend integration tests

Must cover:

- `GET /api/dashboard/command-view`
- filtered anomalies list behavior
- departments index and department detail endpoints
- reports history endpoint
- export rerun endpoint
- refresh current-status endpoint

## Risks

- v2 can accidentally centralize too much logic into one shell container if the
  page boundaries are not preserved
- route-state handling can drift if query building is not centralized
- UI terms like `Attention Count` can diverge from backend field naming if the
  adapter layer is skipped
- responsive drawer behavior can become a second navigation implementation if
  desktop and mobile do not share the same nav model
- reports export rerun can quietly bypass snapshot consistency if it does not
  reuse the same export-service contract

## Decisions locked by this document

- v2 uses a shared sidebar analytics shell
- v2 remains desktop-first but responsive
- dashboard is a command view, not a long-scroll overview
- department detail is the primary investigation destination
- reports is an export center, not only an archive
- route-state and time-range handling are explicit modules
- v2 task planning should be split into dedicated v2 module files, not merged
  into historical v1 task trackers
