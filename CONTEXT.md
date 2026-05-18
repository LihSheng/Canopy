# Context

## Glossary

### Dashboard

The executive landing workspace inside the analytics shell. It is the default
overview page, not a generic container for every nested analysis flow.

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

### Data connector

An app-owned source registration that produces datasets inside HERD Aggregator.
_Avoid_: Host agent, upstream source system

### Connector lifecycle

The app-owned state flow for pausing, archiving, restoring, soft-deleting, and permanently deleting a data connector record inside HERD Aggregator.
_Avoid_: Host uninstallation, upstream decommissioning

## Relationships

- A **Data connector** produces one or more datasets.
- A **Connector lifecycle** changes the app-owned connector record and related HERD Aggregator resources, not the upstream system or host machine.

## Example dialogue

> **Dev:** "Should deleting a **Data connector** run `systemctl stop` on the customer's server?"
> **Domain expert:** "No — the **Connector lifecycle** records and gates app-owned decommissioning only; host cleanup is an admin checklist outside automated app execution."

## Flagged ambiguities

- "Data source decommissioning" can mean upstream/host removal or HERD Aggregator connector lifecycle. Resolved: implement HERD Aggregator **Connector lifecycle** first; do not automate upstream writes or host commands.
