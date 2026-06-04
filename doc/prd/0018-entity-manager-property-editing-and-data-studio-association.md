# PRD: Entity Manager Property Editing and Data Studio Association

Status: draft

Builds on and refines:

- PRD 0015 Entity Manager Registry, Detail, and Editor Split
- PRD 0017 Entity-First Digital Twin Manager

## Problem Statement

PRD 0017 established the Entity-first model and the code now has a working
Entity module. That solved the broad product direction, but the current
boundary is still too loose for day-to-day use.

The user now needs a stricter operating model:

- Entity Manager is the only place where Entity properties are created,
  renamed, removed, required, or otherwise edited
- Entity Manager is the only place where cleaned source data is mapped into
  Entity properties
- Data Studio handles raw source onboarding, cleaning, and source preparation
- Data Studio may show which Entity a dataset feeds, but it does not own Entity
  schema editing
- Entity-to-Entity semantic editing stays in Entity Manager, not in Data Studio

Without this split, the product still feels like dataset tooling with Entity
labels layered on top. Users need a clear place to define the business object
and a separate place to prepare the source data that feeds it.

## Solution

Make Entity Manager the canonical authoring surface for the Entity model and
make Data Studio a source preparation surface with read-only Entity association
context.

The target product shape is:

- Entity Manager
  - define and edit canonical properties
  - bind cleaned source fields to properties
  - manage property metadata such as display name, type, required flag, and
    inclusion state
  - manage Entity review and publish
  - show broken or missing bindings for recovery
- Data Studio
  - manage raw connections, datasets, and cleaning workflows
  - show which Entity a dataset version is associated with
  - provide an entrypoint into Entity Manager for association or bootstrap
  - avoid editing Entity schema directly

This is not a general ETL builder. Data Studio remains the source-preparation
surface. Entity Manager remains the semantic editing surface.

## User Stories

1. As a data modeler, I want to edit Entity properties in Entity Manager, so
   that I can work in the canonical semantic surface.
2. As a data modeler, I want to add a new Entity property, so that the object
   can grow with the business.
3. As a data modeler, I want to rename a property without recreating it, so
   that its identity stays stable.
4. As a data modeler, I want to mark a property required or optional, so that
   publish rules can validate the minimum contract.
5. As a data modeler, I want to bind cleaned source fields from Data Studio to
   Entity properties, so that raw data feeds the Entity without owning it.
6. As a data modeler, I want to see unbound or broken bindings in Entity
   Manager, so that I can repair them without losing semantic intent.
7. As a data modeler, I want Data Studio to show which Entity a dataset feeds,
   so that I can understand downstream usage before editing source data.
8. As a data modeler, I want to open Entity Manager from Data Studio, so that
   I can move from source prep into semantic editing without hunting for the
   right page.
9. As a data modeler, I want Data Studio to stay focused on cleaning and source
   prep, so that raw data work does not get mixed with semantic modeling.
10. As a platform operator, I want Entity editing to live in one surface, so
    that permissions, validation, and review are easier to reason about.
11. As a platform operator, I want Data Studio to avoid Entity schema editing,
    so that the source-prep boundary stays clear.
12. As a future feature owner, I want Entity Manager and Data Studio to have
    narrow, explicit contracts, so that the product can evolve without
    reintroducing coupling.

## Implementation Decisions

- Entity Manager owns:
  - property create/update/delete
  - property display name edit
  - property type and required/optional state
  - property inclusion/exclusion
  - source-field-to-property binding
  - recovery of broken or missing source bindings
  - review and publish flows
- Data Studio owns:
  - raw source ingestion
  - dataset refresh and cleaning
  - source preparation for downstream Entity use
  - read-only display of Entity association context
- A dataset version may be associated with one Entity, but that association is
  informational in Data Studio and authoritative in Entity Manager.
- The Data Studio UI may provide an `Open in Entity Manager` or `Add to Entity`
  entrypoint, but it must not become the primary Entity editor.
- Entity property edits are persisted as part of the Entity revision / semantic
  mapping record, not as a separate Data Studio-side schema.
- Source bindings must point to cleaned or prepared source outputs, not raw
  source-system semantics.
- Entity-to-Entity relationships remain part of Entity Manager if they exist at
  all. Data Studio does not own relationship editing.
- The graph canvas remains the primary Entity authoring layout inside Entity
  Manager.
- The Data Studio surface can display a simple association summary:
  - linked Entity name
  - active Entity version
  - associated source dataset version
  - last published state

## Scope

In scope:

- create new Entity properties
- edit property metadata
- bind cleaned source data to properties
- surface broken binding recovery
- expose Entity association from Data Studio
- deep-link from Data Studio into Entity Manager
- keep Data Studio source-prep and Entity editing boundaries separate

Out of scope:

- raw source cleaning inside Entity Manager
- dataset schema editing inside Entity Manager
- full Entity instance browsing
- generalized ETL transformations in the Entity canvas
- Entity-to-Entity relationship authoring from Data Studio
- cross-tenant Entity management

## Testing Decisions

- Backend tests should cover:
  - property create/update/delete behavior
  - required/optional validation
  - binding persistence and recovery
  - publish blocking when required properties are unresolved
  - association read models exposed to Data Studio
- Frontend tests should cover:
  - Entity Manager property editing states
  - binding add/edit/remove flows
  - broken binding rendering
  - Data Studio association summary and navigation entrypoint
  - empty states when no Entity is associated
- Integration tests should prove that:
  - a property edit in Entity Manager does not require Data Studio schema edits
  - Data Studio can show the linked Entity without becoming the editor
  - source prep changes do not silently mutate Entity schema

## Further Notes

This PRD narrows the 0017 model into a stricter product boundary:

1. Data Studio prepares the source.
2. Entity Manager defines the business object.
3. Entity Manager maps cleaned source data into properties.
4. Data Studio shows association, but does not own Entity editing.

This is the enhancement layer the current implementation needs if the goal is
to keep Entity modeling central and keep source work inside Data Studio.
