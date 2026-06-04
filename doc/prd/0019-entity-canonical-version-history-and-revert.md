# PRD: Entity Canonical Version History and Revert

Status: draft

Builds on:

- PRD 0017 Entity-First Digital Twin Manager
- PRD 0018 Entity Manager Property Editing and Data Studio Association

## Problem Statement

The current Entity experience has two related gaps:

1. The Entity detail surface and the Entity graph/canvas surface do not always
   agree on the same property source-link configuration, version, or publish
   state.
2. A published Entity version can be shown, but the user cannot reliably see
   the full version history or revert to a prior version.

That means the system behaves like multiple partial views of Entity config
rather than one canonical versioned model.

The user-visible symptoms are:

- Entity detail shows one published version while the graph canvas shows a
  different configuration or source-link set.
- property mappings drift between surfaces instead of reading from one shared
  source of truth.
- previous published versions are not clearly browsable.
- reverting to a known-good version is not a first-class action.
- version state is visible in the UI, but version control semantics are not
  complete enough to support audit, rollback, or recovery.

This weakens trust in the Entity surface. If the user cannot tell which config
is authoritative, the page is not acting as a managed semantic model.

## Solution

Introduce a canonical Entity version history model and make both the detail page
and graph canvas read from the same versioned configuration source.

The target product shape is:

- one canonical Entity version record per saved semantic state
- one active published version at a time
- one shared read model for Entity detail and Entity graph/canvas
- explicit version history with prior published states visible
- a revert action that restores a selected prior version as the next draft or
  published state, while preserving history

The Entity detail page should not maintain its own hidden copy of source-link or
property configuration. The graph canvas should not independently invent its own
version state. Both must resolve to the same stored Entity version snapshot for
the selected Entity.

Versioning should behave like managed source control for the semantic model:

- draft edits create a new draft version or draft snapshot
- publish promotes a specific snapshot to the active published state
- previous published versions remain visible in history
- revert creates a new version state based on the selected historical snapshot
  rather than mutating the old published record in place

## User Stories

1. As a data modeler, I want the Entity detail page and graph canvas to show
   the same property links and version state, so that I can trust the config I
   am editing.
2. As a data modeler, I want one canonical source of truth for Entity version
   data, so that different screens cannot drift.
3. As a data modeler, I want to see the full published version history, so that
   I understand how the Entity evolved over time.
4. As a data modeler, I want to open an older published version, so that I can
   inspect what was live before.
5. As a data modeler, I want to revert to a prior version, so that I can recover
   from a bad publish without rebuilding the Entity by hand.
6. As a data modeler, I want revert to preserve history, so that the rollback
   itself is auditable.
7. As a data modeler, I want the published state to be explicit, so that I can
   tell which version is currently active.
8. As a platform operator, I want the detail page and canvas to use the same
   read model, so that the UI cannot display conflicting semantic state.
9. As a platform operator, I want version history to be immutable once
   published, so that audit and recovery remain reliable.
10. As a platform operator, I want revert to create a new versioned state
    rather than overwrite history, so that the full lineage stays intact.
11. As a future feature owner, I want Entity version control semantics to be
    explicit, so that additional review, diff, and rollback features can build
    on the same model.

## Implementation Decisions

- Introduce a canonical Entity version snapshot model that stores:
  - property definitions
  - source-link declarations
  - computed property configuration
  - relationship/link configuration
  - publish metadata
- Treat the Entity detail page and graph canvas as read/write surfaces over the
  same canonical version snapshot.
- Replace any surface-local config cache with a shared versioned read model.
- Make the currently published version an explicit pointer to one canonical
  snapshot.
- Keep prior published versions in a browsable history list.
- Add a revert action that:
  - selects a historical version
  - creates a new editable state based on that version
  - preserves the old version in history
  - updates the active published pointer only after the new state is confirmed
    as the intended live version
- Ensure property/source-link mismatch cannot occur because each surface must
  resolve the same version ID and same version payload.
- Keep the source of truth for version history in the backend, not in browser
  state or per-page local caches.
- Keep publish and revert operations explicit user actions, not automatic
  side effects of navigation.

## Scope

In scope:

- canonical Entity version history
- shared source of truth for Entity detail and graph canvas
- browse previous published versions
- inspect a prior version
- revert from a prior version
- make published state explicit
- eliminate surface-specific version drift

Out of scope:

- runtime entity instance browsing
- source-system mutations
- automatic merge conflict resolution for simultaneous edits
- cross-tenant version comparison
- changing the broader Entity Manager product split

## Testing Decisions

- Backend tests should cover:
  - version snapshot creation
  - version list ordering
  - published pointer updates
  - history preservation after revert
  - detail and canvas readbacks returning the same snapshot payload
  - no accidental mutation of prior published versions
- Frontend tests should cover:
  - detail and canvas rendering the same version metadata
  - history list visibility
  - revert entrypoint and confirmation flow
  - post-revert UI refresh to the new active version
- Integration tests should prove that:
  - a version published from one surface is visible identically on the other
  - reverting from history produces a new active state without losing history
  - a stale or mismatched local cache cannot make detail and canvas diverge

## Further Notes

This PRD treats the two reported issues as one product failure:

1. the UI is not anchored to a single canonical Entity version snapshot
2. the version model is missing proper history and revert semantics

Fixing only the canvas or only the detail page would leave the underlying
contract broken. The product needs one versioned semantic source of truth first,
then both surfaces can render and edit against it consistently.
