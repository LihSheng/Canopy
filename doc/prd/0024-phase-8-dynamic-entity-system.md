# PRD: Phase 8 Dynamic Entity System

Status: draft

## Problem Statement

Canopy is ready to move beyond hardcoded domain types and toward a runtime
Entity system.

Today the product can map source data into fixed business objects, but it does
not yet have a full Entity platform that can:

- define Entities as first-class business objects
- materialize published Entities at runtime from source data
- version and publish Entity definitions safely
- resolve direct relationships between published Entities
- support same-Entity computed properties with deterministic formulas
- keep draft work separate from published runtime behavior
- preserve a stable contract for downstream analytics and future platform
  phases

Without this step, Canopy remains a shaped data model rather than a governed
Entity system.

The product needs a runtime Entity layer that is more than configuration:

- users must be able to author Entities with properties, links, and computed
  fields
- published Entities must materialize predictably from source data
- draft edits must not break live readers
- validation must protect runtime behavior before publish

This PRD defines the Phase 8 Entity system itself, not the later linked-Entity
formula, aggregate formula, or incremental materialization optimizations.

## Solution

Build a Phase 8 Entity system that makes Entities first-class runtime objects.

The system will provide:

- Entity schema and editor surfaces
- source binding configuration per Entity property
- runtime materialization for published Entities
- draft/publish governance with version history
- one active published version per Entity
- direct link resolution for published Entities
- same-Entity computed properties with deterministic formulas
- validation gates that block publish on invalid runtime definitions

The Phase 8 materialization model will start with:

- full snapshot replace
- one active source binding at runtime
- direct links only
- 1:1 and 1:M cardinality only
- published targets only

The Phase 8 computed-property model will support:

- direct field transforms
- simple deterministic functions
- explicit null handling
- same-Entity references only

The Phase 8 computed-property model will not support:

- linked-Entity formulas
- aggregate formulas across related Entities
- custom user-defined functions
- incremental upsert materialization

The product outcome should be:

- a user can create an Entity from source data
- a user can define properties, links, and same-Entity computed fields
- a user can save drafts without immediately breaking publish safety
- a user can publish a valid Entity and have it materialize at runtime
- runtime readers can use latest-published by default and pin a specific
  version when needed
- deprecated Entities remain available in historical views without polluting
  normal creation flows

## User Stories

1. As a data modeler, I want to create an Entity, so that I can model a
   business object explicitly instead of relying on hardcoded domain types.

2. As a data modeler, I want to define properties on an Entity, so that the
   object has a stable business surface.

3. As a data modeler, I want to define property keys and display names
   separately, so that technical identity stays stable when labels change.

4. As a data modeler, I want to save drafts before publishing, so that I can
   work incrementally.

5. As a data modeler, I want publish validation to block invalid definitions,
   so that broken Entities do not reach runtime.

6. As a data modeler, I want one active published version per Entity, so that
   downstream readers always have one stable runtime contract.

7. As a data modeler, I want version history to remain visible, so that I can
   audit how an Entity evolved over time.

8. As a data modeler, I want runtime materialization to happen after publish,
   so that the published Entity becomes usable immediately.

9. As a data modeler, I want materialization to start with a full snapshot
   replace, so that runtime behavior is easy to reason about.

10. As a data modeler, I want to bind one active source at runtime, so that the
    first release stays deterministic.

11. As a data modeler, I want planned bindings to remain visible after publish,
    so that future data sources are not forgotten.

12. As a data modeler, I want planned bindings to reference only published
    Entities, so that runtime dependencies stay stable.

13. As a data modeler, I want to declare direct links between Entities, so that
    related business objects can be traversed explicitly.

14. As a data modeler, I want only direct 1:1 and 1:M links in Phase 8, so
    that the initial runtime model stays simple.

15. As a data modeler, I want link cardinality to be validated before publish,
    so that declared relationships are trustworthy.

16. As a data modeler, I want optional links to be allowed, so that incomplete
    relationships do not block modeling entirely.

17. As a data modeler, I want optional links to resolve later when data appears,
    so that temporary gaps do not require manual republish.

18. As a data modeler, I want linked Entities to remain separate references, so
    that Phase 8 does not blur Entity boundaries with inherited fields.

19. As a data modeler, I want computed properties on the same Entity, so that
    I can express derived business meaning without leaving the Entity model.

20. As a data modeler, I want computed properties to support simple
    deterministic functions, so that common formula cases do not require custom
    code.

21. As a data modeler, I want computed properties to support explicit null
    handling, so that the formula behavior is predictable.

22. As a data modeler, I want syntax errors to be blocked in draft, so that I
    do not accumulate broken formulas.

23. As a data modeler, I want publish validation to block semantic errors, so
    that invalid formulas never reach runtime.

24. As a data modeler, I want formulas to use stable internal field identity,
    so that renaming a field does not break the Entity contract.

25. As a data modeler, I want deleted source fields to trigger recovery mapping
    before publish fails, so that simple drift can be repaired safely.

26. As a data modeler, I want computed properties to appear in the Entity detail
    UI as first-class fields, so that derived values are part of the model.

27. As a data modeler, I want computed properties to be edited in a dedicated
    formula editor, so that complex logic has one safe entrypoint.

28. As a data modeler, I want formula dependency changes to warn in draft and
    fail on publish, so that I can keep working while still protecting runtime.

29. As a platform operator, I want runtime readers to default to the latest
    published version, so that interactive browsing stays simple.

30. As a platform operator, I want the ability to pin to a specific published
    version, so that downstream consumers can stay stable.

31. As a platform operator, I want published versions to be immutable, so that
    audit and rollback stay reliable.

32. As a platform operator, I want deprecated Entities to remain available in
    historical views, so that old contracts remain inspectable.

33. As a platform operator, I want normal creation flows to hide deprecated
    Entities, so that authors do not accidentally reuse old contracts.

34. As a platform architect, I want same-Entity computed properties to stay in
    Phase 8, so that linked-Entity and aggregate formulas can land later with
    separate dependency models.

35. As a platform architect, I want linked-Entity formulas to be deferred to a
    later phase, so that cross-Entity dependency tracking is not rushed.

36. As a platform architect, I want aggregate formulas to be deferred to a
    later phase, so that cross-Entity counting and summarization can be designed
    deliberately.

37. As a platform architect, I want incremental materialization to be deferred
    to a later optimization phase, so that Phase 8 proves the full snapshot
    replace path first.

38. As an operator, I want tombstones hidden from normal reads, so that the
    runtime Entity view stays clean.

39. As an operator, I want tombstones preserved in audit and materialization
    state, so that delete history remains recoverable.

40. As a product owner, I want Phase 8 to unlock real runtime Entities, so that
    the platform becomes a true Entity system instead of a config-only editor.

## Implementation Decisions

- Use `Entity` as the product term in UI and PRD language.
- Keep the runtime Entity model draft/publish based with version history.
- Allow exactly one active published version per Entity.
- Let runtime readers default to latest-published, with version pinning where
  needed.
- Require every publish to create a new immutable version.
- Keep published versions indefinitely unless a future retention policy says
  otherwise.
- Materialize published Entities with a full snapshot replace path first.
- Defer incremental upsert materialization to a later optimization phase.
- Allow one active source binding at runtime for Phase 8.
- Show inactive bindings as planned bindings in the UI.
- Require planned bindings to reference only published Entities.
- Keep planned bindings editable only through a new draft version.
- Allow runtime link resolution only for published Entities.
- Restrict Phase 8 runtime links to direct links only.
- Support only 1:1 and 1:M links in Phase 8.
- Validate link cardinality at publish time and fail publish on mismatch.
- Allow optional links, but require them to be explicitly marked optional.
- Let optional links resolve later when data appears.
- Keep linked Entities as explicit references, not inherited-property sources in
  Phase 8.
- Support same-Entity computed properties only in Phase 8.
- Allow direct field transforms and simple deterministic functions in Phase 8.
- Allow explicit null handling and helper functions like `coalesce` and `if`.
- Block linked-Entity formulas, aggregate formulas, and custom user-defined
  functions in Phase 8.
- Require a dedicated formula editor for computed properties.
- Block syntax errors on draft save.
- Block semantic and runtime errors on publish.
- Use stable internal field identities for formulas.
- Add a recovery mapping step when source fields are deleted or renamed before
  publish failure becomes hard.
- Warn in draft when dependencies change, but fail publish on unresolved issues.
- Expose computed properties as first-class fields in the detail UI, while
  visually grouping them separately from base properties.
- Treat deprecated Entities as historical and inspectable, but hide them from
  normal creation flows.
- Keep tombstones out of normal reads and only expose them in audit and
  materialization state.
- Defer linked-Entity formulas to Phase 8.5.
- Defer aggregate formulas to Phase 9.5.
- Defer incremental materialization to Phase 8.6.

## Testing Decisions

- Good tests verify external behavior: draft save, publish validation, runtime
  materialization, link resolution, formula evaluation, version pinning, and
  deprecation behavior.
- Test the Entity system through API and service seams, not private model
  internals.
- Test publish validation separately from draft save behavior.
- Test same-Entity computed properties with direct transforms, simple
  deterministic functions, null handling, and invalid field references.
- Test link resolution for published Entities only, with direct 1:1 and 1:M
  links.
- Test runtime materialization using full snapshot replace semantics.
- Test version history, latest-published defaults, and explicit version pinning.
- Test that invalid drafts remain saveable but cannot publish.
- Test that deprecated Entities stay visible in history and hidden in normal
  create flows.
- Prior art in the repo includes entity mapping, entity detail, relationship
  link, entity canvas, and publish-related tests in the existing PRD family.
- Preferred seams are Entity repository, publish service, materialization
  service, formula engine, link resolver, and detail/publish API routes.

## Out of Scope

- Linked-Entity formulas
- Aggregate formulas across related Entities
- Incremental upsert materialization
- Custom user-defined functions for formulas
- Many-to-many links in Phase 8
- Inherited-property exposure from linked Entities
- Property-value search across Entities
- Search on computed-property values
- Cross-Entity formula dependency tracking
- Cross-Entity recompute orchestration
- Full analytics and dashboard builder work
- AI-assisted ontology generation

## Further Notes

- Phase 8 is the first runtime Entity release, not just a configuration editor.
- Phase 8.5 is reserved for linked-Entity formulas.
- Phase 8.6 is reserved for incremental materialization.
- Phase 9.5 is reserved for aggregate formulas.
- The roadmap and the PRD should stay aligned with the same-Entity / linked-
  Entity / aggregate split.
- The runtime Entity model should remain snapshot-consistent so downstream
  analytics and AI can continue to rely on stable published versions.
