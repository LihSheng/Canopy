# V2 UI/UX Design

## Purpose

This document captures the agreed v2 UI/UX direction for the analytics
experience.

It is not a visual design-system replacement for [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md). It defines layout,
navigation, hierarchy, page behavior, and interaction rules that v2 should
implement while staying inside the established design language.

## Scope

This document covers the shared analytics shell and these user-facing areas:

- `Dashboard`
- `Anomalies`
- `Departments`
- `Reports`
- `Profile`

It does not define:

- backend architecture changes
- data model changes
- anomaly-rule changes
- export pipeline changes
- mobile-first redesign

## Design direction

V2 should be a moderate redesign in the same design language.

Required design alignment:

- follow [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md)
- keep the interface light, calm, and content-led
- use the existing pill, card, spacing, and typography language
- improve hierarchy and navigation without creating a new brand direction

V2 should optimize for:

- faster executive decision-making
- more usable workspace on desktop
- clearer drill-down from summary to investigation

V2 should not optimize for:

- visual novelty for its own sake
- deep configuration or widget customization
- heavy interaction inside charts

## Shared analytics shell

### Navigation model

V2 replaces the top-navigation-first analytics layout with a sidebar shell.

Sidebar rules:

- sidebar is for navigation only
- primary items are:
  - `Dashboard`
  - `Anomalies`
  - `Departments`
  - `Reports`
- sidebar is stable across all analytics pages
- no secondary contextual sub-navigation in v2
- sidebar top shows brand or product identity only
- no KPI strip in the sidebar
- sidebar bottom utility zone contains:
  - `Profile`
  - `Logout`

### Sidebar behavior

- desktop default is expanded
- user can collapse sidebar to icon rail
- collapsed sidebar uses tooltips only
- collapse toggle lives beside the brand at the top of the sidebar
- active item uses a soft filled state, not a thin border treatment
- sidebar stays light, not dark

### Responsive behavior

V2 is desktop-first, but responsive.

Responsive rules:

- desktop is the primary design target
- on smaller screens, sidebar becomes an overlay drawer
- overlay drawer keeps the same item order and labels as desktop
- v2 does not require a separate mobile-first information architecture

### Header pattern

Top-level analytics pages use one standard lightweight header pattern:

- title on the left
- optional small context text under the title
- operational controls on the right

Nested/detail pages may add breadcrumb above or near the page title.

Breadcrumb rules:

- breadcrumb appears only on nested/detail pages
- breadcrumb shows location, not filter state
- breadcrumb stays lightweight and secondary

## Operational area

Navigation does not live in the top header anymore.

The top-right operational area should stay tight and focused.

Dashboard header controls:

- time-range control
- refresh control and status
- export action

Operational rules:

- `Data Refresh` is not a sidebar destination
- refresh remains in the operational area
- export can be triggered from the dashboard header
- complex export history and export-center behavior belong in `Reports`

### Time-range behavior

Dashboard and investigation pages use a quick time-range control, not only a
raw month picker.

Rules:

- one active page-wide time range at a time
- cards, panels, charts, and ranking on a page use the same active range
- current range is also shown in header context
- deeper pages may still offer more contextual filtering later, but v2 keeps a
  single visible primary range

## Dashboard

### Role

`Dashboard` is the fixed executive landing view inside the analytics shell.

It should always return to the same default command view instead of restoring
arbitrary previous dashboard state.

### Layout intent

V2 changes the dashboard from a long-scroll overview into a tighter
above-the-fold command view.

The dashboard should answer:

- what needs attention now
- whether spend and risk moved materially
- where the user should investigate next

### First-screen structure

Recommended structure:

- left: dominant `Top Attention Items` panel
- right: 2x2 summary-card block
- second band: `AI Summary` and `Trend Chart`
- third band: compact department ranking preview

### Summary cards

V2 dashboard uses four summary cards:

- `Total Spend`
- `Payroll Spend`
- `Claims Spend`
- `Attention Count`

Rules:

- cards show big number plus short delta or change context
- no mini sparklines in v2
- only `Attention Count` is clickable in v2
- `Attention Count` links to `Anomalies` and carries the current time range
- other three cards stay informational in v2

### Dominant attention panel

The dashboard hero panel is a prioritized attention panel, not a trend chart.

Rules:

- show top 3 prioritized items
- do not visibly group them by severity on the dashboard
- each row shows:
  - department name
  - severity
  - one-line reason
  - one change-percentage chip
- include `View all anomalies` action
- clicking an item opens department detail with relevant context pre-applied

### AI summary

The dashboard AI summary is supporting interpretation, not the hero.

Rules:

- position it below the top command band
- use hybrid format:
  - one sentence headline
  - 2 to 3 bullets
- no `View full explanation` action in v2

### Trend chart

The dashboard trend chart is supporting context.

Rules:

- show `Total`, `Payroll`, and `Claims`
- read-only in v2
- no chart click or drill interaction in v2

### Department ranking preview

The dashboard ranking is a compact preview, not the full comparison workspace.

Rules:

- show top 5 departments
- each row shows:
  - department name
  - spend
  - change %
  - attention state
- clicking a row opens department detail directly
- include `View all departments` action
- claim breakdown is secondary and should be de-emphasized or moved out if
  layout pressure appears

## Anomalies

### Role

`Anomalies` becomes a triage workspace, not only a larger version of the
dashboard list.

### Page structure

The page should go straight into filters and the triage list.

Rules:

- no summary strip at the top
- page stays focused on triage and drill-down

### Controls and grouping

Rules:

- prioritize severity and time-range triage
- group rows by severity
- `High` group expanded by default
- `Medium` and `Low` start collapsed

### Row anatomy

Each anomaly row should stay compact.

Required row content:

- department
- severity
- change %
- one-line reason

### Interaction

Rules:

- anomaly rows support inspect and drill-down only
- no `mark reviewed` or `dismiss` workflow in v2
- clicking a row opens department detail

## Departments

### Role

`Departments` is a ranked index for comparison and investigation.

It is a destination page, not an expandable sidebar list.

### Page structure

The page should go straight into controls and ranked results.

Rules:

- no summary strip at the top
- no side-by-side time-range comparison in v2
- one selected time range only

### Controls

Top controls should prioritize:

- search
- attention filter
- time range
- sort

Sorting rules:

- default sort is highest attention level
- UI exposes one primary sort only
- no advanced multi-sort UI in v2

### Ranked list style

The page uses a hybrid analytical row or card style.

Each row should show:

- department name
- total spend
- change %
- attention indicator

Attention-bearing rows should use stronger emphasis plus badge, not badge only.

## Department detail

### Role

Department detail is the primary investigation destination for both dashboard
and anomalies flows.

It is a full detail page inside the same analytics shell.

### Navigation and header

Rules:

- department detail is a nested page
- breadcrumb is shown here
- page keeps a visible time-range control
- page remains a single long-scroll flow
- no internal tabs in v2

### Content order

Recommended order:

1. department summary header
2. dominant trend and change panel
3. smaller department-level AI summary
4. split contributor view

### Summary header

Header should include:

- department name
- attention state
- total spend
- change %
- current time-range context

### Dominant panel

The hero panel on department detail is a trend and change panel.

This is where trend becomes primary, unlike the main dashboard.

### Department-level AI summary

Rules:

- smaller than the main dashboard AI summary
- placed below the trend panel
- hybrid format again:
  - one sentence summary
  - 2 bullets preferred
- should explain:
  - what changed
  - likely drivers
  - what to review next

### Contributor split view

V2 shows two equal analytical panels side by side:

- top employees
- top claim types

Rules:

- equal visual weight
- same active time range
- no detailed transaction table in v2 first

### CTA back into anomaly triage

Department detail includes `View related anomalies`.

Rules:

- CTA opens `Anomalies`
- department and current time range are pre-applied
- anomaly triage remains in the anomaly workspace, not inline on department
  detail

## Reports

### Role

`Reports` is an export center, not only an archive page.

It should feel like a proper operational workspace inside the same shell.

### Page structure

Rules:

- no summary strip at the top
- show export presets first
- show recent exports after that

### Export model

V2 supports manual exports only.

Rules:

- no scheduled exports in v2
- dashboard header export uses quick presets
- richer export history and re-run flows live here

### Presets

The v2 export presets are:

- `Executive Summary`
- `Department Spend`
- `Anomaly Review`

### History rows

Recent export rows should include:

- preset or export type
- created time
- status
- source context:
  - preset name
  - time range
  - snapshot timestamp

### Row actions and failures

Rules:

- completed exports support:
  - `Download`
  - `Run again`
- failed exports remain inline in the same history list
- failed rows show clean user-facing summaries
- deeper error details can be opened on demand

## Profile

`Profile` should be a lightweight page inside the same shell.

Rules:

- accessed from sidebar bottom utility zone
- not a dropdown-only or modal-only treatment
- leaves room for future account or preference surfaces

## V2 non-goals

V2 should not include:

- dashboard widget customization
- internal dashboard sub-navigation
- clickable or drillable dashboard trend chart
- anomaly review-state workflow
- scheduled exports
- detailed transaction table on department detail
- mobile-first redesign as a separate design track

## Implementation implications

This UI/UX direction implies:

- shared shell components across `Dashboard`, `Anomalies`, `Departments`,
  `Reports`, and `Profile`
- consistent page-header composition
- route and state handling for time-range carry-over between pages
- explicit drill-down links from attention, ranking, and anomalies surfaces
- responsive sidebar behavior without changing the core information architecture

Implementation should stay aligned with:

- [`ARCHITECTURE.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/ARCHITECTURE.md)
- [`DESIGN.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/DESIGN.md)
- [`doc/v2/plan.md`](C:/Users/Lih%20Sheng/Documents/HERD%20Aggregator/doc/v2/plan.md)
