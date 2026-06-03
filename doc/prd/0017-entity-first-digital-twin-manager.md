# PRD: Entity-First Digital Twin Manager

Status: draft

Supersedes parts of:

- PRD 0013 Entity Canvas Cutover and Admin Feature Flags
- PRD 0015 Entity Manager Registry, Detail, and Editor Split

## Problem Statement

The current Entity flow in Canopy is still rooted in dataset workspace
authoring. That shape was acceptable for the first semantic configuration
slice, but it breaks the product model the user now expects.

The user expectation is closer to a Palantir-style ontology workflow:

- an Entity is a digital twin of a real-world business object
- the Entity owns its canonical properties and relationships
- source data from Data Studio is attached to that Entity as bindings
- the canvas is where the user defines business meaning first, then links raw
  data into that meaning

The current product does not satisfy that model.

Today, the system still behaves like this:

- semantic mapping mutation is dataset-scoped
- Entity detail is mostly an inspection page
- editing routes back into dataset workspace
- deleted source datasets can strand an Entity in an orphaned state
- source structure is still treated as the primary owner of semantic config

That creates several user-visible problems:

- users cannot truly manage an Entity as a first-class business object
- orphaned Entities are hard or impossible to recover from the Entity surface
- business schema and source bindings are coupled too tightly
- multi-source business concepts are awkward because the model still centers
  one dataset editing surface
- the product feels like dataset mapping with Entity labels, not Entity
  management with source bindings

Canopy needs to move to an Entity-first model where the digital twin is the
stable center and Data Studio assets are bound into it through explicit,
governed, versioned source bindings.

## Solution

Add a first-class Entity Manager to Canopy and make Entity the primary owner of
semantic modeling.

The target product shape is:

- Entity Registry for discovery
- Entity Manager / Detail for inspection, draft editing, review, and publish
- Entity-first graph canvas as the main authoring surface
- Data Studio as source onboarding and source discovery, not the sole semantic
  authoring owner

The new model should treat:

- Entity as the stable digital twin of a real-world business object
- Entity schema as business-owned
- source bindings as implementation-owned links from Data Studio assets into
  Entity properties
- published Entity versions as governed, reproducible semantic contracts

The product should support:

- blank-canvas Entity creation
- dataset-driven `Add to Entity` bootstrap flows
- multi-source Entities
- required and optional canonical properties
- one active published version per Entity
- draft editing through forked revisions
- broken binding recovery without deleting the Entity definition
- review and diff before publish
- exact dependency pinning to stable published dataset versions
- hard-block protection against deleting published source dependencies

This is not a free-form ETL surface. Heavy cleaning remains in Data Studio.
Entity Manager owns semantic modeling, canonical property definition,
lightweight binding transforms, relationship declarations, review, and publish.

## User Stories

1. As a data modeler, I want to create an Entity from a blank canvas, so that I
   can define the business object before source data is attached.
2. As a data modeler, I want an Entity to represent a real-world object, so
   that the product matches my mental model of a digital twin.
3. As a data modeler, I want Entity schema to be business-first, so that raw
   table shape does not control the meaning of the object.
4. As a data modeler, I want to define canonical properties on an Entity, so
   that business semantics stay stable across source changes.
5. As a data modeler, I want to create optional properties before binding them,
   so that I can enrich the model incrementally.
6. As a data modeler, I want to mark some properties as required, so that
   publish validation enforces the minimum usable contract.
7. As a data modeler, I want property display names to be editable, so that the
   Entity stays understandable to users.
8. As a data modeler, I want property keys to stay stable after publish, so
   that downstream semantics do not break from casual renaming.
9. As a data modeler, I want properties to have stable internal identities, so
   that rename is not misinterpreted as delete-and-recreate.
10. As a data modeler, I want Entity display names to be editable, so that the
    business label can evolve without changing semantic identity.
11. As a data modeler, I want Entity keys to stay stable after publish, so that
    links and downstream references remain durable.
12. As a data modeler, I want to open a central Entity Registry, so that I can
    discover and manage Entities without remembering source datasets first.
13. As a data modeler, I want to search Entities by key, name, status, and
    source usage, so that I can find the right digital twin quickly.
14. As a data modeler, I want Entity detail to show draft and published state,
    so that I understand what is live and what is still being edited.
15. As a data modeler, I want to fork a draft from the published Entity, so
    that I can change semantics without mutating the live contract.
16. As a data modeler, I want exactly one published Entity version at a time,
    so that all downstream reads stay on one stable contract.
17. As a data modeler, I want draft history to be preserved, so that I can
    review what changed over time.
18. As a data modeler, I want one active draft per Entity, so that concurrent
    editing conflicts are controlled.
19. As a data modeler, I want draft locks to show who is editing, so that the
    team understands ownership of in-progress changes.
20. As a data modeler, I want stale draft lock takeover rules later, so that
    the model does not get stuck forever.
21. As a data modeler, I want the Entity canvas to show source nodes and
    canonical properties in one graph, so that semantic intent and source
    implementation are visible together.
22. As a data modeler, I want to attach multiple source nodes to one Entity, so
    that real multi-table business concepts can be modeled accurately.
23. As a data modeler, I want one property to support a direct single-source
    binding, so that simple mappings stay simple.
24. As a data modeler, I want one property to support computed behavior later,
    so that multi-source business fields can be modeled without forcing ETL
    hacks.
25. As a data modeler, I want one source field to feed multiple properties when
    intentional, so that reuse is possible without artificial duplication.
26. As a data modeler, I want duplicate source-field reuse to be visible in the
    review experience, so that suspicious fan-out is not hidden.
27. As a data modeler, I want canonical property types to be user-owned, so
    that business meaning survives source type drift.
28. As a data modeler, I want bind-time type validation, so that incompatible
    source links are visible before publish.
29. As a data modeler, I want light semantic transforms near the binding, so
    that small modeling adjustments do not require upstream rewiring.
30. As a data modeler, I want heavy cleaning to remain in Data Studio, so that
    Entity Manager does not become an uncontrolled ETL tool.
31. As a data modeler, I want to start an Entity from Data Studio using `Add to
    Entity`, so that source-driven bootstrapping remains fast.
32. As a data modeler, I want blank-canvas creation and dataset-driven
    bootstrapping to end in the same manager, so that the product has one
    canonical editing surface.
33. As a data modeler, I want relationships between Entities to live in the
    same canvas, so that the digital twin graph stays coherent.
34. As a data modeler, I want link declarations to stay narrower than a full
    execution engine, so that first release remains governable.
35. As a data modeler, I want draft Entities to allow incomplete or broken
    bindings, so that in-progress work is not blocked.
36. As a data modeler, I want publish to fail when required properties are
    unresolved, so that only usable contracts go live.
37. As a data modeler, I want optional properties to remain unbound in a
    published Entity, so that the model can evolve incrementally without fake
    data wiring.
38. As a data modeler, I want publish to require at least one valid binding, so
    that a published Entity is executable, not just conceptual.
39. As a data modeler, I want broken source bindings to stay visible on the
    Entity instead of being auto-removed, so that semantic work is recoverable.
40. As a data modeler, I want orphaned Entities to be repairable from the
    Entity Manager, so that deleting or changing source assets does not strand
    the business model.
41. As a data modeler, I want published bindings to pin exact stable dataset
    versions, so that Entity behavior is reproducible and auditable.
42. As a data modeler, I want one published Entity to use multiple pinned
    dataset versions, so that cross-domain business models are practical even
    when source refresh cadences differ.
43. As a data modeler, I want Entity drafts to be able to reference draft
    source assets during editing, so that modeling work can happen before final
    source publication.
44. As a data modeler, I want publish to block when active bindings still point
    to unstable source assets, so that live semantics never depend on mutable
    upstream drafts.
45. As a data modeler, I want a review and diff step before publish, so that I
    can inspect semantic impact before cutover.
46. As a data modeler, I want review to speak in Entity terms rather than raw
    JSON deltas, so that semantic changes are understandable.
47. As a data modeler, I want raw structured diff to remain available as a
    supporting detail, so that technical users can audit the stored change.
48. As a data modeler, I want downstream impact previews before publish, so
    that I can see what dashboards, exports, and links may be affected.
49. As a platform operator, I want dataset deletes hard-blocked when a
    published Entity depends on them, so that Canopy cannot recreate orphaned
    production semantics.
50. As a platform operator, I want dataset-version deletes hard-blocked when a
    published Entity depends on them, so that published contracts stay
    reproducible.
51. As a platform operator, I want draft-only source dependencies to be allowed
    to break without corrupting published behavior, so that editing and
    production remain separate.
52. As a platform operator, I want Entity Manager to preserve the product term
    `Entity` while backend seams can stay `semantic_*` or equivalent internal
    names, so that UX language and implementation language stay consistent.
53. As a platform operator, I want entity-first modules to remain narrow and
    testable, so that the transition away from dataset-scoped ownership does
    not create a monolith.
54. As a platform operator, I want product reads to stay on published contracts
    only, so that dashboards, exports, and AI remain stable and snapshot-safe.
55. As a future feature owner, I want the Entity Manager to feel Palantir-like
    in flow, so that users model business objects first and bind data second,
    without importing unsupported runtime behavior.

## Implementation Decisions

- The product term remains `Entity`. The implementation may retain existing
  internal naming where necessary, but the behavior shifts to an Entity-first
  semantic ownership model.
- Entity becomes the primary owner of semantic modeling. Dataset workspace is
  no longer the sole authoritative owner of editability.
- Data Studio remains the primary source onboarding and source preparation
  surface.
- Entity Manager becomes the primary semantic authoring and governance surface.
- The transition should be implemented in two slices:
  - slice 1: backend/domain foundation, orphan recovery, standalone Entity
    editing shell, publish governance, dependency protection
  - slice 2: full Entity-first canvas manager with multi-source node editing,
    richer binding UX, and stronger impact tooling
- An Entity is the digital twin of a real-world business object.
- Entity schema is business-owned and source-independent.
- Source bindings are implementation-owned references from Data Studio assets
  into Entity properties.
- Entity identity model:
  - immutable internal Entity id
  - stable Entity key
  - editable display name
- Entity Property identity model:
  - immutable internal property id
  - stable property key
  - editable display name
- A normal rename is a true rename of the same Entity or property, not a
  delete-and-recreate event.
- Changing Entity key or property key after publish is an explicit breaking
  migration, not a casual edit.
- Each Entity supports:
  - many historical revisions
  - zero or one active draft
  - exactly one active published version
- Editing a published Entity always forks a new draft revision first.
- Product reads only consume the active published Entity version.
- Draft editing is single-editor for the first release:
  - one active draft per Entity
  - one edit lock holder at a time
  - other users can view but not mutate the draft
- The new authoring model supports both:
  - blank-canvas Entity creation
  - Data Studio `Add to Entity` entrypoints with source nodes preloaded
- The canonical authoring destination is the same Entity Manager in both entry
  flows.
- The canvas should model:
  - an Entity node
  - property nodes
  - source nodes
  - relationship links
  - computed-property inputs later in the same graph model
- Multiple source nodes can bind into one Entity.
- For first governed release, a property binding should use an explicit
  strategy rather than an ambiguous free-form many-to-one merge.
- The first release should prioritize:
  - direct single-source property bindings
  - computed property support
- Fallback/precedence-driven multi-binding is deferred until the strategy model
  is intentionally designed.
- Source field reuse across multiple properties is allowed, but must remain
  visible in the UX and review flow.
- Canonical property types are user-owned.
- Binding validation checks source compatibility against canonical type.
- Light semantic transforms may live in Entity Manager at the binding layer.
- Heavy data preparation remains in Data Studio. Examples that stay upstream:
  - major row reshaping
  - cross-table data prep joins as ETL
  - broad cleanup pipelines
  - source-specific normalization logic
- Draft state may contain:
  - unbound optional properties
  - broken bindings
  - incomplete modeling
  - draft source references
- Publish requires:
  - at least one valid source binding
  - all required properties resolved validly
  - all active source dependencies pinned to exact stable published dataset
    versions
- Optional properties may remain unbound in published state and resolve to null
  in downstream reads.
- Published Entity versions may pin multiple stable dataset versions at once.
- A published Entity stores its full source dependency set explicitly.
- Published Entity behavior must not read mutable latest source state. It reads
  the pinned dependency set.
- Broken source bindings are retained visibly on the Entity model. They are not
  auto-removed.
- Orphan recovery is part of the core product requirement. Missing source
  dataset or missing source field must remain recoverable from Entity Manager.
- Relationship modeling remains in the same canvas, but is secondary to getting
  property/source binding flow correct.
- Relationship scope in this PRD remains config-oriented. No executable graph
  action engine is introduced here.
- Review and publish are separate from freeform editing.
- Publish requires an explicit review/diff step.
- The primary diff model is semantic/domain-first:
  - entity metadata changes
  - property adds/removes/renames/type changes
  - binding changes
  - transform changes
  - relationship changes
  - dependency-set changes
  - broken/unbound warnings
- Raw structured diff may be shown as a supporting technical view.
- A third-party diff library may be used only as a rendering helper. Product
  semantics must remain owned by Canopy's domain model and review logic.
- Downstream impact preview should be shown before publish, even if the first
  implementation is lightweight.
- Delete protection rules:
  - deleting a dataset is hard-blocked if any published Entity depends on it
  - deleting a dataset version is hard-blocked if any published Entity depends
    on it
  - draft-only dependencies may break and surface as broken draft bindings
- The implementation should keep architectural seams narrow:
  - registry/listing read model
  - detail/read model
  - draft lifecycle service
  - publish/review service
  - dependency protection service
  - source binding resolver/validator
  - canvas DTO and persistence seam
- The product must remain read-only toward upstream operational systems. This
  feature only governs Canopy-owned semantic contracts and source references.
- This PRD intentionally changes prior dataset-scoped assumptions. Older PRDs
  that keep dataset workspace as the authoritative semantic owner should be
  treated as superseded where they conflict with this document.

## Testing Decisions

- Good tests should verify externally visible behavior and semantic outcomes,
  not implementation details or internal component structure.
- The most important tests in this feature are contract and state-transition
  tests, because the risk is semantic corruption rather than visual polish.
- Backend tests should focus on:
  - Entity draft creation from published state
  - single active draft lock behavior
  - publish validation rules
  - exact one-published-version rule
  - broken binding retention behavior
  - source dependency pinning behavior
  - dataset and dataset-version delete protection for published dependencies
  - orphan recovery APIs and state transitions
  - relationship validation behavior
  - canonical property identity stability across rename
  - Entity key/property key migration guard behavior
- Frontend tests should focus on:
  - Entity Registry discovery and navigation behavior
  - Entity detail and manager loading states
  - blank-canvas creation flow
  - `Add to Entity` entry flow from Data Studio
  - draft fork flow from published Entity
  - lock-state UI behavior
  - broken-binding recovery UX
  - review and diff rendering
  - publish gating behavior
  - downstream impact preview rendering
  - delete-block messaging when published dependencies exist
- Canvas tests should cover domain behavior, not node-position implementation
  trivia.
- Review/diff tests should assert semantic summaries, not brittle serialized
  text blocks.
- Delete-protection tests should cover both draft-only dependency cases and
  published dependency cases.
- Prior art in the codebase includes:
  - existing semantic API and validation integration tests
  - existing entity registry and detail tests
  - existing dataset delete and dataset workspace tests
  - existing entity canvas and mapping flow tests
- The first implementation wave should prioritize test coverage for modules
  with governance risk:
  - publish rules
  - dependency protection
  - orphan recovery
  - revision state model
- A good regression test should prove the product cannot reintroduce the
  original orphan problem for published Entity dependencies.

## Out of Scope

- A full runtime ontology execution engine
- A general-purpose ETL or transformation builder inside Entity Manager
- Real-time collaborative multi-user draft editing with merge resolution
- Full fallback precedence strategy for multi-binding in the first release
- Automatic downstream migration of breaking key changes
- Entity instance explorer/runtime object browsing
- A fully generic ontology query language
- AI-authored Entity schema or binding rules
- Automatic source deletion repair for published Entity contracts
- Cross-tenant Entity authoring or browsing beyond current tenant boundaries
- Replacing Data Studio as the source onboarding and heavy preparation surface
- Rewriting the entire backend naming model away from existing internal
  `semantic_*` terms in the same wave

## Further Notes

This PRD defines the product move from dataset-centric semantic mapping toward
Entity-first digital twin management.

The core product doctrine is:

1. Model the business object first.
2. Define canonical properties and relationships on that object.
3. Bind Data Studio assets into the object through explicit source bindings.
4. Review semantic change before publish.
5. Publish one governed live version at a time.
6. Protect published dependencies from destructive upstream deletes.

This direction should feel Palantir-like in user flow:

- Entities are first-class
- source data is attached into them
- graph modeling is central
- published semantics are governed

But it should still respect Canopy architecture:

- read-only toward source systems
- modular monolith seams
- snapshot-safe downstream usage
- explicit dependency ownership

If issue-tracker publishing is unavailable in the local runtime, this PRD file
is the detailed source-of-truth artifact for later issue creation and slicing.
