# Context

## Glossary

### Dataset
A structured collection of data produced by a **Data connector**.

### Dataset Version
An immutable snapshot of a **Dataset** corresponding to a specific import or re-import event.

### Active Version
The specific **Dataset Version** currently used by the system for reports and analysis.

### Superseded Version
A **Dataset Version** that was previously an **Active Version** but has been replaced by a more recent version. It remains fully accessible and inspectable.

### Invalid Version
A **Dataset Version** record created during a failed import/re-import process, marked with the reason for failure. It is not considered for analysis.

### Mapped Column
A column in a **Dataset** that has been explicitly linked or configured for use within the system (e.g., for joins, filters, or specific transformations).


### Attention item

A prioritized issue shown to executives because it needs review. An attention
item may be backed by an anomaly today, but the term is intentionally broader
than anomaly so future risk signals can use the same UI pattern.

### Attention count

The summary-card count of items that currently require executive review. This
term is preferred over anomaly count in the dashboard UI because it is more
executive-friendly and does not overfit the design to one implementation type
of signal.

### Analytics shell

The shared application frame used across Dashboard, Anomalies, Departments,
and Reports. It includes sidebar navigation, a lightweight page header, and a
main content canvas.

### Tenant switcher

The in-shell control that lets a user change the active tenant context after
login. The shell shows the current tenant name; the picker lists the user's
available tenants.

### Active tenant

The tenant currently scoped for the session and dashboard data. A user may
belong to multiple tenants, but only one active tenant is used at a time.

### Data connector

An app-owned source registration that produces datasets inside Canopy Intelligence.
_Avoid_: Host agent, upstream source system

### Connector lifecycle

The app-owned state flow for pausing, archiving, restoring, soft-deleting, and permanently deleting a data connector record inside Canopy Intelligence.
_Avoid_: Host uninstallation, upstream decommissioning

## Relationships

- A **Data connector** produces one or more datasets.
- A **Connector lifecycle** changes the app-owned connector record and related Canopy Intelligence resources, not the upstream system or host machine.

## Example dialogue

> **Dev:** "Should deleting a **Data connector** run `systemctl stop` on the customer's server?"
> **Domain expert:** "No — the **Connector lifecycle** records and gates app-owned decommissioning only; host cleanup is an admin checklist outside automated app execution."

## Flagged ambiguities

- "Data source decommissioning" can mean upstream/host removal or Canopy Intelligence connector lifecycle. Resolved: implement Canopy Intelligence **Connector lifecycle** first; do not automate upstream writes or host commands.
