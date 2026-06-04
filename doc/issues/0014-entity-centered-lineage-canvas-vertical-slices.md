# Issues: Entity-Centered Lineage Canvas

Status: draft

Parent: `doc/prd/0021-entity-centered-lineage-canvas.md`

These slices move the Entity canvas from dataset-scoped mapping behavior to an
Entity-centered lineage graph with room for future derived depth.

1) **Entity-centered lineage graph contract**
- Type: AFK
- Blocked by: None
- User stories covered: 1, 2, 4, 5, 6, 7, 8, 9, 18, 20, 21, 22, 26, 27
- What to build: Introduce a generic lineage graph contract for Entity Manager
  that treats the Entity as the center, keeps Dataset and Dataset Version as
  visible upstream context, and represents source nodes, derived nodes, and
  simple links in one storage-friendly shape. The first slice should define the
  node and edge kinds, the direct upstream path semantics, and the draft
  revision read model needed by the canvas.
- Acceptance criteria:
  - [ ] The graph model supports node kinds for dataset, source, derived, and entity
  - [ ] The graph model supports edge kinds for lineage, binding, and link
  - [ ] The read model can describe an Entity-centered graph with Dataset and Dataset Version visible
  - [ ] Existing Entity revision data can be mapped into the new generic graph contract
  - [ ] Backend tests cover the new graph contract and read-model shape

2) **Entity canvas renders lineage path**
- Type: AFK
- Blocked by: Slice 1
- User stories covered: 1, 2, 3, 4, 5, 6, 7, 8, 9, 15, 16, 17, 18
- What to build: Rework the Entity detail canvas so it renders the Entity at
  the center, shows Dataset and Dataset Version as upstream nodes, shows source
  nodes feeding into the Dataset Version, and displays property labels and
  simple entity links without requiring a legacy dataset-backed mapping to be
  present.
- Acceptance criteria:
  - [ ] The Entity canvas appears for a draft Entity that has revision data but no legacy dataset mapping
  - [ ] The Entity stays centered in the canvas
  - [ ] Dataset and Dataset Version are visible by default
  - [ ] Source nodes connect into Dataset Version, not directly into Entity
  - [ ] Entity properties remain visible as labels on the Entity node
  - [ ] Simple entity links remain visible as edges
  - [ ] Frontend tests cover rendering for both mapped and draft-only Entities

3) **Derived lineage collapse and expansion**
- Type: AFK
- Blocked by: Slice 1, Slice 2
- User stories covered: 11, 12, 13, 14, 15, 23, 24
- What to build: Add support for rendering existing derived lineage nodes,
  collapsing derived chains into summary nodes, and expanding them again. The
  first release should default to fully expanded and only apply collapse rules
  to derived chains.
- Acceptance criteria:
  - [ ] Existing derived nodes render when they are present in stored lineage data
  - [ ] Derived chains can collapse and expand in the canvas
  - [ ] Collapsed derived chains summarize with last visible label plus hidden-step count
  - [ ] The canvas loads fully expanded by default
  - [ ] Collapse behavior is limited to derived chains only
  - [ ] UI tests cover collapse and expand behavior

4) **Publish flow without legacy dataset gate**
- Type: AFK
- Blocked by: Slice 1, Slice 2
- User stories covered: 1, 2, 26, 28, 30, 31
- What to build: Remove the old requirement that publish depends on a
  dataset_id-backed association. Keep publish governed by draft revision
  validity and optional dependency pinning, while allowing valid Entity drafts
  to publish even when the legacy mapping link is absent.
- Acceptance criteria:
  - [ ] Publish succeeds for a valid draft without a dataset_id-backed mapping
  - [ ] Optional source dependency pinning still works when provided
  - [ ] Frontend does not block publish solely because dataset_id is missing
  - [ ] Backend publish tests pass for both dependency-free and dependency-pinned flows
  - [ ] Regression coverage proves Employee-style drafts can publish without the legacy gate

5) **Entity canvas regression guardrails**
- Type: AFK
- Blocked by: Slice 1, Slice 2, Slice 3, Slice 4
- User stories covered: 1, 2, 7, 8, 16, 17, 18, 25, 26, 27, 28
- What to build: Add end-to-end regression coverage for the new Entity canvas
  semantics so future changes do not reintroduce dataset-centered rendering or
  the legacy dataset_id publish dependency.
- Acceptance criteria:
  - [ ] The canvas still renders when the Entity has draft revision data but no saved legacy mapping
  - [ ] The canvas still renders Dataset and Dataset Version as upstream context
  - [ ] Derived-chain collapse behavior stays limited to derived nodes
  - [ ] Publish remains independent from the legacy dataset gate
  - [ ] Tests cover the main Entity detail page and the backend publish path

## Publishing Notes

- Issue tracker publishing is not performed from this draft because tracker
  configuration and triage label vocabulary were not provided in this thread.
- If publishing later, apply `needs-triage` to each issue and publish in
  dependency order: Slice 1, Slice 2, Slice 3, Slice 4, Slice 5.

