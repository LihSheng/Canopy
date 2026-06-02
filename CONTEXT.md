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

### Sync mode

The per-dataset policy that determines how data moves from a third-party source into Canopy Intelligence. Values: `batch` (scheduled pull), `real_time` (accelerated polling, future CDC), `direct_query` (no copy — query source live at request time).

### Batch strategy

The sub-policy for `batch` sync mode datasets. Values: `full_snapshot` (wipe and repull all rows) or `incremental_cursor` (pull only rows where a timestamp column exceeds the last sync cursor).

### Cursor column

The source table column (auto-detected from schema, user-overridable) used by incremental cursor pulls to determine which rows are new or changed since the last sync.

### Data Studio

The configuration section in the analytics shell sidebar where users manage Connections and Datasets. Separate from the consumption-oriented Dashboard, Departments, Anomalies, and Reports sections.

### Entity
The business-object configuration a user defines for a dataset version inside the graph-based Data Studio workspace. Entity is the user-facing term for the semantic configuration model, and the canvas is the primary authoring surface.

### Object Type
The tenant-scoped reusable business-object definition that an Entity mapping can select or create. Object Types are shared across dataset versions within the tenant.

### Relationship Link
An optional metadata declaration inside an Entity mapping that connects the current Entity to another tenant Object Type using a source property and the target Object Type's primary key.
Phase 1 uses a visual, canvas-based editor for link layout and interaction, while the stored link remains metadata in the Semantic Mapping.
Phase 1 graph scope shows source, dataset version, and Entity nodes only; clean/group/process nodes are deferred.
Phase 1 graph edits are authoritative for the mapping config, so saved graph changes must update the Semantic Mapping record.
Phase 1 graph changes are committed through an explicit Save/Publish action and produce a new versioned mapping record.
Phase 1 graph version snapshots include both semantic config and canvas layout state so the graph can reopen in the same arrangement.
Phase 1 canvas scope shows the current dataset graph plus target references only; it does not become a tenant-wide graph.
Phase 1 canvas uses separate node types for raw source object, dataset version, Entity/Object Type, and target references.
Phase 1 node inspector edits the Entity/Object Type mapping; source and dataset version nodes stay read-only.
Phase 1 uses the graph as the primary workspace and reuses wizard logic in a graph-side inspector instead of keeping two separate editors.
Phase 1 uses a right-side drawer for node and edge inspection/editing.
Phase 1 graph load shows the current dataset lineage path, the current Entity, and existing links/references.
Phase 1 graph supports designing an Entity from the canvas by adding one or more raw data source nodes and linking their fields into the Entity.
Phase 1 edges connect source fields to Entity properties, not just source nodes to Entity nodes.
Phase 1 source fields are collapsed inside the source node by default and expanded in the drawer when the source is selected.
Phase 1 uses a one-source-field-to-one-Entity-property rule for mapping and does not support computed multi-field properties yet.
Phase 1 source nodes include dataset tables and static files.
Phase 1 canvas can create new source nodes from the graph so non-technical users can start from the Entity workspace instead of only attaching pre-imported sources.
Phase 1 source creation from the canvas uses a lightweight setup drawer rather than the full Data Studio import wizard.
Phase 1 source nodes are reusable across multiple Entities.
Phase 1 Entities can connect to multiple source nodes.
Phase 1 source nodes are an unordered set in the Entity config.
Phase 1 canvas source creation only registers already known table/file sources; it does not start a full new connector import flow.

### Semantic Mapping
The versioned configuration record that stores one Entity's Object Type selection, primary key, property mappings, and relationship links for a specific dataset version.
_Avoid_: Admin panel, settings page

### Connection Wizard

The 3-step UI flow inside Data Studio for adding a new data source: authenticate (enter credentials and test), select objects (tick tables to import), configure sync policy (choose sync mode and batch strategy per selected table).

### SecretStore

The encryption interface that protects third-party database credentials at rest. The runtime implementation uses AES-256-GCM with an application key; the interface is designed for a future swap to AWS Secrets Manager without schema or service changes.

### Live Explorer

A future module (separate from the snapshot-based dashboard) that hosts Direct Query datasets with their own auto-refresh and freshness indicators. Queries the source database in real time; never feeds analytics, exports, or AI summaries.

### Source object

The upstream database object a dataset imports from. In v1 this is a table name, identified as `connection_id + source_object_name`.

### Schema signature

A canonical, normalized representation of a source object’s column schema (column name, type details, and nullability) plus a derived hash. Used to detect schema drift.

### Schema drift

Any detected difference between the current discovered schema of a source object and the last stored **schema signature**. Drift types include: added column, removed column, renamed column, type change (including nullability, string length, numeric precision/scale, timestamp timezone).

### Schema drift event

An immutable record of a schema drift detection with before/after details and a computed delta. Used for auditability, UI surfacing, and alerting.

### Schema drift block

The dataset-level circuit breaker state applied when breaking schema drift is detected. While blocked, affected datasets are skipped by sync/materialization until reviewed and cleared.

## Relationships

- A **Data connector** produces one or more datasets.
- A **Dataset** carries a **sync mode** and optional **batch strategy** and **cursor column**.
- A **Dataset** references a **Source object** via `connection_id + source_object_name`.
- A **Connection Wizard** creates a **data connector** and its associated **datasets** through a 3-step flow.
- A **Connector lifecycle** changes the app-owned connector record and related Canopy Intelligence resources, not the upstream system or host machine.
- **Data Studio** hosts the **Connection Wizard** and presents the connection/dataset catalog to the user.
- A **Dataset** can carry an **Entity** mapping for one dataset version.
- An **Entity** selects or creates one **Object Type**.
- A **Semantic Mapping** stores the versioned configuration for an **Entity**.
- A **Relationship Link** connects one **Entity** to another tenant **Object Type**.
- The **Entity Designer Graph Canvas** is the primary config surface; separate Entity and Graph tabs are not the target end state.
- The legacy `Entity` tab can remain as an alias that routes into the graph surface during the transition period.
- **Live Explorer** will host **direct_query** datasets in a separate module outside the snapshot pipeline.
- The **SecretStore** encrypts third-party credentials stored in the **data connector** config.
- A **Schema signature** is stored per **Source object** and compared during discovery and sync runs.
- A breaking **Schema drift** triggers a **Schema drift block** on affected datasets and emits a **Schema drift event**.

## Example dialogue

> **Dev:** "Should deleting a **Data connector** run `systemctl stop` on the customer's server?"
> **Domain expert:** "No — the **Connector lifecycle** records and gates app-owned decommissioning only; host cleanup is an admin checklist outside automated app execution."

## Flagged ambiguities

- "Data source decommissioning" can mean upstream/host removal or Canopy Intelligence connector lifecycle. Resolved: implement Canopy Intelligence **Connector lifecycle** first; do not automate upstream writes or host commands.

- "Direct Query" datasets return live source data that may diverge from the snapshot backing the dashboard, export, and AI summary. Resolved: Direct Query datasets go into a separate **Live Explorer** module, not the executive dashboard; the dashboard remains snapshot-consistent.
