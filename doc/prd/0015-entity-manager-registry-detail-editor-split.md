# PRD: Entity Manager Registry, Detail, and Editor Split

Status: draft

## Problem Statement

The current Entity experience is embedded inside dataset detail. That makes the
feature discoverable only if a user already knows which dataset to open. It also
mixes three different jobs into the same place:

- browsing all entity definitions
- inspecting one entity in detail
- editing the dataset-scoped semantic mapping that produced that entity

That shape works for first implementation, but it does not scale well for user
navigation or for future refactoring.

The product needs a central Entity area that feels closer to Palantir's
Ontology Manager pattern:

- a place to discover and search all entities
- a place to inspect one entity across its properties, computed properties, and
  links
- a place to open the authoring surface for the dataset version that owns the
  config

The implementation also needs to stay modular. If the registry, detail view,
editor, and future explorer are tightly coupled, the code will become hard to
move, split, or replace later.

## Solution

Add a central Entity area to Canopy with clear module boundaries.

The initial split should be:

- Entity Registry: browse and search all entities
- Entity Detail: inspect one entity and its backing mappings
- Entity Editor: edit the dataset-scoped semantic config for one dataset
- Entity Explorer: browse entity instances later, once runtime entity browsing
  exists

The registry and detail pages should be the primary discoverability layer. The
dataset workspace should remain the authoring entry point for mapping a dataset
into an entity. The editor should be reusable, but not responsible for
registry, discovery, or instance browsing.

This is intentionally not a monolithic "all-in-one" page. Each module should be
independent enough that it can be moved, replaced, or tested in isolation.

## User Stories

1. As a data studio user, I want one place to see all entities, so that I do
   not need to remember which dataset created each one.
2. As a data studio user, I want to search entities by name, key, dataset, or
   updated time, so that I can find the right entity quickly.
3. As a data studio user, I want to see recent and frequently used entities,
   so that I can return to active work without extra navigation.
4. As a data studio user, I want to open an entity detail page, so that I can
   inspect its properties, computed properties, and links in one place.
5. As a data studio user, I want to see which dataset version backs an entity,
   so that I understand where the configuration came from.
6. As a data studio user, I want to jump from an entity detail page to the
   underlying dataset mapping, so that I can edit the authoritative config.
7. As a data studio user, I want the dataset workspace to remain an authoring
   entry point, so that first-time mapping still starts from the dataset I am
   working on.
8. As a data studio user, I want the editor to be reusable from multiple
   entry points, so that I can open the same authoring surface from the dataset
   or from the central entity area.
9. As a data studio user, I want to see properties, computed properties, and
   links without opening a different tool, so that the entity stays easy to
   understand.
10. As a data studio user, I want the future entity explorer to be separate
    from the editor, so that browsing instances does not clutter mapping.
11. As a platform operator, I want a clean entity registry boundary, so that
    the list/search experience can evolve without changing the editor.
12. As a platform operator, I want the entity detail page to use a stable read
    model, so that it can be cached, tested, and moved independently.
13. As a platform operator, I want the entity editor to depend on narrow API
    contracts, so that it can be swapped or refactored without rewriting the
    registry.
14. As a platform operator, I want the registry, detail, and editor modules to
    share contracts instead of shared internal state, so that module boundaries
    stay clean.
15. As a platform operator, I want the dataset-scoped mapping logic to remain
    isolated from the registry logic, so that ownership stays explicit.
16. As a future feature owner, I want the entity explorer to be added later
    without changing the registry or editor contracts, so that the product can
    expand safely.
17. As a future feature owner, I want the central entity area to resemble a
    manager rather than a one-off page, so that the product language stays
    consistent with the ontology model.
18. As a future feature owner, I want entity modules to be independently
    replaceable, so that large refactors do not force a full rewrite.

## Implementation Decisions

- Introduce a central entity area as a first-class product surface.
- Keep dataset detail as the authoring entry point for semantic mapping.
- Keep the entity editor reusable, but not responsible for discovery or
  instance browsing.
- Split the surface into separate modules for registry, detail, editor, and
  future explorer.
- Use a browse-first registry as the canonical landing page for all entities.
- Use a detail page to assemble the entity summary from narrow read models.
- Keep the editor tied to the dataset version that owns the mapping record.
- Avoid a single shared "entity mega-page" that mixes registry, detail, and
  authoring concerns.
- Make each module communicate through stable DTOs and route params rather than
  shared UI state.
- Keep module dependencies one-directional:
  - registry can open detail or editor
  - detail can open dataset mapping or editor
  - editor returns saved mapping data to detail or registry
  - explorer remains separate from authoring
- Keep registry, detail, and editor logic independently testable.
- Keep data access narrow and role-specific instead of creating a generic
  entity service that knows everything.
- Preserve the dataset-scoped, versioned semantic mapping model as the source
  of truth for edits.
- Preserve the current meaning of `Entity` in the UI and `semantic_*` in the
  backend where already established.

## Testing Decisions

- Good tests verify external behavior, not component internals or hidden
  implementation details.
- The registry should be tested as a search-and-navigation surface.
- The detail page should be tested as a read model assembled from entity and
  dataset mapping data.
- The editor should be tested for save/reopen behavior and contract stability.
- Navigation from registry to detail, and from detail to editor, should be
  covered as user flows.
- The dataset workspace should keep its own tests for authoring entry behavior.
- Modules to test:
  - entity registry search and filtering
  - entity detail data loading and backlinks
  - entity editor save/reopen flow
  - dataset workspace entry routing
  - route alias behavior between central entity pages and dataset mapping
- Prior art:
  - existing dataset entity mapping tests
  - existing entity canvas and wizard tests
  - existing admin and dashboard route tests

## Out of Scope

- A single monolithic page that combines registry, detail, editor, and
  explorer
- Runtime entity instance browsing
- Executable joins from links
- Cross-tenant entity browsing
- Reworking the semantic storage model
- Moving dataset-scoped authoring out of the dataset workspace immediately
- A full ontology action/explorer system

## Further Notes

The product direction should feel Palantir-like without copying the worst
coupling patterns.

The recommended long-term shape is:

1. Central entity registry for discovery
2. Entity detail for inspection and backlinks
3. Dataset-scoped editor for authoritative mapping changes
4. Entity explorer later for runtime object browsing

This split keeps the product understandable to users and keeps the code easier
to move later because each module has one reason to change.
