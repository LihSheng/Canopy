# PRD: Foundry / Ontology Platform Hardening

Status: draft

## Problem Statement

Canopy already has the main platform surfaces that resemble a Foundry-style
data and ontology workflow:

- source connections and dataset ingestion
- deterministic cleaning and normalization
- dataset workspace and lineage views
- entity mapping and relationship declarations
- analytics, anomalies, refresh, export, and AI summary surfaces
- tenant platform modules
- admin operational health dashboard

What it does not yet have is the same depth, rigor, and governance expected
from a production-grade ontology platform.

Today the main product gaps are:

- core data APIs are not consistently tenant-scoped and role-scoped
- audit coverage is partial and not strong enough for governance workflows
- operational telemetry exists but does not cover the full platform
- entity and relationship config exists, but runtime ontology behavior is still
  config-only
- relationship contracts are not pinned strongly enough for long-lived object
  semantics
- cleaning and lineage are deterministic but still prototype-scale for large,
  explainable, enterprise-grade data operations

This creates a mismatch between the product surface and the trust level users
expect when they think of a Palantir Foundry-like system:

- operators expect strong permissions and tenant isolation
- data stewards expect durable lineage and auditability
- ontology users expect stable business objects and governed relationships
- platform admins expect reliable operational visibility
- product teams expect action APIs and downstream extensions to sit on safe,
  explicit contracts

Canopy needs a platform-hardening program that strengthens these foundations
without violating the existing architecture rules:

- never write back to the source system
- deterministic analytics decide, LLM narrates
- dashboard, export, and AI stay on the same snapshot basis

## Solution

Deliver a cross-cutting hardening program across nine capability areas:

1. Data integration
2. Data cleaning / transformation
3. Business objects
4. Object relationships
5. Business rules
6. Permissions
7. Action APIs
8. Audit logs
9. Operational dashboard

The program will not replace Canopy's current architecture. It will deepen the
existing seams so the current modules behave like a governed platform instead
of a feature-complete but lightly enforced prototype.

The resulting product behavior should be:

- every project, connection, dataset, entity, run, export, and admin action is
  tenant-aware and role-aware
- every important operator or user mutation is auditable with structured,
  queryable event metadata
- every major background workflow emits persisted telemetry that appears in the
  operational health dashboard
- entity mappings evolve from config-only design artifacts toward durable
  runtime-ready ontology contracts
- relationship links become stable, versioned business-object contracts rather
  than loose metadata
- cleaning stays deterministic but gains stronger scale, explainability, and
  governance seams
- action APIs become explicit platform actions with clear read-only vs
  state-changing boundaries
- admin and platform operators can understand what happened, who did it, and
  what data or tenant it affected

This PRD defines the full enhancement set as one umbrella platform program.
Implementation can still be shipped as multiple vertical slices.

## User Stories

1. As a tenant user, I want every project, connection, and dataset API to
   return only data I am allowed to access, so that tenant isolation is real.
2. As a tenant user, I want unauthorized dataset IDs and connection IDs to be
   rejected even when I know the raw identifiers, so that object access is not
   guessable.
3. As a tenant admin, I want role-based controls for operational and semantic
   actions, so that not every authenticated user can perform governance work.
4. As a platform admin, I want admin-only routes to enforce both admin identity
   and valid tenant context where needed, so that platform operations stay
   scoped and safe.
5. As a suspended or revoked user, I want access to stop as soon as my
   membership no longer applies, so that stale tokens do not preserve access.
6. As a data engineer, I want connection discovery, dataset creation, dataset
   refresh, and dataset deletion to be scoped to the correct tenant and
   project, so that multi-tenant routing is not accidental.
7. As a data engineer, I want data integration objects to carry explicit tenant
   ownership, so that routing, filtering, auditing, and metrics stay coherent.
8. As a data engineer, I want schema drift, connection health, and dataset
   health to appear in the same governed surface, so that operational review is
   centralized.
9. As a data engineer, I want source discovery and dataset materialization to
   emit telemetry, so that slow or failing pipelines show up in platform ops.
10. As a data engineer, I want per-connection and per-dataset operational
    history, so that I can troubleshoot changes over time.
11. As a data steward, I want every semantic mapping save to record actor,
    tenant, dataset, version, and change metadata, so that ontology config is
    auditable.
12. As a data steward, I want object type changes to be audited, so that
    business-object definitions have governance history.
13. As a data steward, I want relationship link changes to be audited, so that
    object graph changes are reviewable.
14. As a data steward, I want entity relationships to resolve against explicit
    target contracts, so that downstream semantics do not drift silently.
15. As a data steward, I want relationship targets to remain understandable
    even after the target entity evolves, so that old mappings stay
    explainable.
16. As a data steward, I want to know whether a relationship points to a
    current contract or an outdated one, so that I can upgrade intentionally.
17. As an ontology consumer, I want business objects to be more than designer
    config, so that I can eventually query stable business entities.
18. As an ontology consumer, I want business objects to have a durable runtime
    contract, so that downstream APIs and analytics can depend on them.
19. As an ontology consumer, I want object identities to be explicit and
    durable, so that joins and references remain stable.
20. As a product owner, I want Canopy to preserve the current config-first
    entity workflow while preparing for runtime ontology use, so that feature
    depth grows without a rewrite.
21. As a platform architect, I want runtime ontology work to reuse existing
    dataset, semantic, and snapshot seams, so that the implementation remains
    modular.
22. As a platform architect, I want runtime object materialization to stay
    read-only against upstream data, so that Canopy never violates source
    immutability.
23. As a data engineer, I want cleaning rules to stay deterministic, so that
    the same input and rule set always yield the same output.
24. As a data engineer, I want cleaning issues to be structured by row, column,
    and rule, so that I can explain exactly what happened.
25. As a data engineer, I want cleaning execution to scale beyond whole-file
    in-memory copies, so that large datasets do not degrade the platform.
26. As a data engineer, I want each cleaning step to expose typed metrics and
    warnings, so that pipeline quality is measurable.
27. As a data engineer, I want cleaning output to retain per-step lineage
    evidence, so that data review is explainable.
28. As a reviewer, I want to know which rows and columns were affected by a
    specific cleaning rule, so that governance review is practical.
29. As a data engineer, I want normalization and mapping stages to reuse
    cleaned-field metadata, so that lineage remains continuous.
30. As a data engineer, I want data integration runs to expose status, timing,
    bytes, rows, and failure reason, so that troubleshooting is fast.
31. As an operator, I want refresh orchestration, exports, schema drift, and
    retention changes to emit telemetry, so that the operational dashboard
    covers the full platform.
32. As an operator, I want telemetry retention and rollup windows to stay
    explicit and tenant-scoped, so that the data-health dashboard is
    predictable.
33. As an operator, I want recent failures to link back to the affected
    dataset, connection, pipeline, and run, so that drill-down is direct.
34. As an operator, I want refresh stages to be visible in telemetry, so that I
    can tell whether failures happened in extract, ontology, analytics,
    anomalies, insights, or publish.
35. As an operator, I want export jobs to emit telemetry and audit events, so
    that expensive reporting work is observable.
36. As an operator, I want connection testing and discovery to emit telemetry,
    so that flaky integrations surface operationally.
37. As an operator, I want admin health data to reflect persisted telemetry
    instead of ad hoc logs, so that the dashboard is trustworthy.
38. As a compliance reviewer, I want important user and admin actions to appear
    in a structured audit log, so that I can answer who-did-what questions.
39. As a compliance reviewer, I want audit events to include resource type and
    resource ID, so that I can filter the audit history by object.
40. As a compliance reviewer, I want audit events to include before/after
    values when settings change, so that mutations are reconstructable.
41. As a compliance reviewer, I want audit events to include a reason where
    review workflows require one, so that governance actions are justified.
42. As a compliance reviewer, I want audit events to include correlation IDs or
    run IDs, so that I can follow one operation across multiple modules.
43. As a compliance reviewer, I want audit events to distinguish read-only
    access from state-changing actions, so that governance reports remain clear.
44. As a product owner, I want action APIs to have clear product meaning, so
    that users understand what the platform can actually do.
45. As a product owner, I want state-changing actions to sit behind explicit
    platform services and contracts, so that the API layer stays thin.
46. As a product owner, I want ontology-related actions to remain config and
    publish actions until runtime object actions are intentionally introduced,
    so that the product does not imply unsupported capability.
47. As a platform maintainer, I want the action model to separate read-only
    analysis actions from administrative mutations, so that permissioning is
    simpler.
48. As a platform maintainer, I want refresh, export, retention, and schema
    drift operations to share common action metadata, so that telemetry and
    audit can be consistent.
49. As an analytics consumer, I want dashboard, export, and AI summary to stay
    on the same snapshot basis, so that I trust the numbers.
50. As an analytics consumer, I want snapshot identity to remain queryable
    across dashboard and export jobs, so that investigation is possible.
51. As an analytics consumer, I want anomalies and dashboard summaries to be
    tenant-safe and snapshot-safe, so that cross-tenant leakage cannot happen.
52. As an analytics consumer, I want business rules to be explicit, testable,
    and independently evolvable, so that analytics logic remains maintainable.
53. As a developer, I want anomaly and business-rule modules to expose simple
    interfaces and typed outputs, so that rule growth does not become a giant
    service file.
54. As a developer, I want platform-hardening changes to reuse deep modules,
    so that behavior is testable without booting the whole application.
55. As a developer, I want authorization and ownership checks to be centralized,
    so that route handlers do not each invent their own access logic.
56. As a developer, I want audit and telemetry emission to be shared seams, so
    that new workflows cannot silently skip governance.
57. As a developer, I want integration, ontology, audit, and telemetry
    contracts to be testable with focused integration tests, so that regression
    risk is controlled.
58. As a release owner, I want this platform-hardening program to be shippable
    in vertical slices, so that value can land incrementally.
59. As a release owner, I want the highest-risk gaps addressed first, so that
    platform trust improves before new ontology features expand surface area.
60. As a future feature owner, I want this hardening work to become the
    foundation for deeper ontology queries, richer admin dashboards, and safer
    action automation, so that future work builds on stable seams.

## Implementation Decisions

- This is an umbrella platform PRD. It defines one coordinated enhancement
  program but should be implemented as multiple slices.

- The highest-priority slice order is:
  1. permissions and tenant ownership hardening
  2. structured audit coverage
  3. telemetry expansion and operational dashboard coverage
  4. ontology contract hardening
  5. cleaning and lineage depth improvements
  6. action API normalization

- Core architectural rules remain unchanged:
  - no upstream write-back
  - deterministic analytics first, LLM narration second
  - snapshot-consistent dashboard/export/AI outputs

- Existing domain vocabulary should stay:
  - product/UI term: `Entity`
  - implementation term: `semantic_*`
  - platform ops route concept: admin data health / operational health

- Permissions and access-control decisions:
  - All project, connection, dataset, semantic, refresh, export, and admin
    routes must enforce authenticated identity plus explicit ownership scope.
  - Tenant-aware routes should require tenant context unless the route is
    intentionally platform-global and admin-only.
  - Project, connection, and dataset records should carry direct `tenant_id`
    ownership in storage, while still preserving their project relationship for
    navigation and grouping.
  - Semantic records should remain tenant-scoped and route through tenant-aware
    object type and dataset version ownership checks.
  - Access checks should move into shared authorization seams rather than being
    reimplemented ad hoc in route handlers.
  - Role checks should distinguish at least:
    - platform admin
    - tenant admin / governance actor
    - standard tenant member
  - Stale token tenant context must be revalidated against current membership.

- Data integration hardening decisions:
  - Connection and dataset records must carry direct tenant ownership metadata
    so tenant-safe querying and auditing do not depend on project joins.
  - Run and related operational records must carry enough ownership metadata to
    enforce tenant-safe querying and auditing.
  - Dataset health remains the natural seam for surfacing source-integrity and
    schema-drift issues.
  - Connection discovery and materialization workflows should emit both audit
    and telemetry records where operationally meaningful.

- Data cleaning / transformation decisions:
  - Cleaning stays deterministic and code-driven.
  - Cleaning execution should move toward chunked or table-oriented processing
    instead of repeated whole-dataset deep copies.
  - Cleaning results should evolve from free-form warning strings to structured
    issue objects with rule, row, column, severity, and message.
  - Step-level metrics should be persisted or otherwise exposed for telemetry
    and quality review.
  - Cleaning lineage should remain compatible with the existing lineage graph
    model but gain stronger traceability metadata.

- Business object decisions:
  - Existing object type and mapping configuration remains the source of truth
    for semantic design.
  - A runtime-ready ontology contract layer should be added without forcing
    immediate full object instance materialization in the first slice.
  - Business objects need stable identifiers, stable primary-key semantics, and
    explicit contract versioning for downstream consumers.
  - Runtime ontology work must remain read-only and snapshot-scoped.

- Object relationship decisions:
  - Relationship links should be treated as durable ontology contracts, not
    only UI metadata.
  - Link targets should resolve against explicit target contracts rather than
    implicitly trusting the latest mapping forever.
  - Relationship compatibility checks should include contract compatibility, not
    only current property type compatibility.
  - Future link consumers should be able to inspect source object, source key,
    target object, target key, cardinality, and contract version.

- Business rule decisions:
  - Business rules should remain in narrow, typed modules.
  - Rule execution outputs should be typed and auditable where relevant.
  - Cross-cutting rule families should avoid growing into monolithic service
    files.
  - Analytics, anomaly, and future ontology evaluation rules should remain
    separable from HTTP and storage details.

- Action API decisions:
  - Platform actions should be modeled explicitly as named actions with common
    metadata.
  - Read-only analytical requests should remain separate from state-changing
    administrative actions.
  - Refresh, export, retention, schema drift clear, connection lifecycle, and
    future ontology publish actions should share common tracing and audit seams.
  - Ontology actions in this program stay within config, validation, publish,
    and governance scope. No upstream operational callbacks.

- Audit log decisions:
  - Audit logs should move toward a structured event contract rather than only
    event-type plus opaque JSON.
  - Audit events should include:
    - tenant scope
    - actor identity
    - resource type
    - resource ID
    - action
    - timestamp
    - correlation/run ID when applicable
    - structured before/after or delta data when applicable
    - optional reason for governance-sensitive operations
  - Core actions requiring audit coverage include:
    - connection lifecycle mutations
    - dataset create/update/delete/reimport/refresh
    - semantic object type and mapping mutations
    - relationship mapping mutations
    - schema drift clear/review actions
    - retention policy changes
    - export triggers and reruns
    - admin impersonation and tenant lifecycle actions
    - sensitive reads such as export download, semantic validation, and admin
      health access where they expose or review governance-sensitive state

- Operational dashboard decisions:
  - Persisted telemetry remains the source of truth for admin data health.
  - Current tenant-scoped, UTC-windowed rollup model remains valid and should
    be extended rather than replaced.
  - Telemetry coverage should expand to refresh, export, semantic, connection,
    and governance workflows.
  - Dashboard drill-down should be able to answer:
    - what failed
    - where it failed
    - when it failed
    - which tenant, connection, dataset, or run was affected
    - what the last successful run looked like
  - Rollups and raw telemetry retention should stay explicit and configurable.
  - The operational health dashboard stays admin-only and remains separate from
    the tenant analytics dashboard.

- Module-level implementation direction:
  - Build or strengthen deep modules around:
    - authorization and ownership resolution
    - audit event recording
    - telemetry emission
    - ontology contract resolution
    - relationship contract validation
    - cleaning execution and issue reporting
  - Route handlers should orchestrate these modules, not own the rules.

- Schema and contract direction:
  - Add tenant ownership where missing on control-plane artifacts that must be
    tenant-scoped.
  - Add structured audit columns/records needed for governance queries.
  - Add telemetry coverage fields only where required for drill-down and rollup.
  - Add ontology contract metadata needed to pin relationship targets.

- UI and API direction:
  - Existing dataset health and admin data-health surfaces should be extended,
    not duplicated.
  - UI should clearly distinguish:
    - read-only observability
    - review-required governance actions
    - state-changing administrative actions
  - Product language should not imply unsupported runtime ontology actions
    until those actions actually exist.

## Testing Decisions

- Good tests assert externally observable behavior:
  - correct authorization outcome
  - correct data scoping
  - correct audit event emission
  - correct telemetry emission
  - correct contract validation
  - correct dashboard/ops responses
  - correct deterministic cleaning outputs
  - correct snapshot-consistent behavior

- Good tests should avoid coupling to implementation details like private helper
  names, internal SQL shape, or intermediate in-memory structures unless those
  structures are themselves the public contract of a deep module.

- Modules to test:
  - authorization and ownership resolution
  - tenant-aware repository/query behavior
  - role-gated administrative actions
  - structured audit recording for major mutations
  - telemetry emission for refresh, export, run, connection, semantic, and
    admin workflows
  - operational dashboard rollup and drill-down behavior
  - ontology contract resolution and relationship pinning behavior
  - relationship compatibility validation
  - deterministic cleaning execution, issue typing, and lineage metadata
  - snapshot consistency between dashboard, export, and AI summary references

- Test split:
  - pure unit tests for validation, contract resolution, rule classification,
    and deterministic cleaning transforms
  - integration tests for repository scoping, API authorization, audit writes,
    telemetry writes, and admin dashboard queries
  - targeted frontend tests for governance and operational surfaces where
    visible behavior changes

- Prior art in the codebase:
  - backend validation-heavy unit tests
  - backend API and persistence integration tests
  - semantic validation tests
  - refresh/orchestration tests
  - admin health tests
  - frontend dashboard and entity flow tests

- Specific test-quality guidance:
  - prefer narrow regression tests around shared seams
  - verify unauthorized access by behavior, not by internal guard method names
  - verify audit and telemetry through persisted outputs and API surfaces
  - verify contract pinning through changed-target scenarios
  - verify cleaning determinism by rerunning same input and comparing outputs

## Out of Scope

- Any workflow that writes back to source systems
- Approvals, task assignment, or operational callbacks into upstream HR systems
- Fully general runtime ontology query language in the first hardening slice
- Automatic relationship inference across datasets
- AI-generated cleaning or ontology rules
- Replacing the current modular monolith with microservices
- Replacing existing dataset workspace and admin dashboard navigation with a
  brand-new IA
- Broad redesign of analytics metrics themselves unless required by scoping,
  audit, or snapshot consistency
- Cross-tenant relationship traversal
- Unbounded action automation without explicit governance and audit controls

## Further Notes

- This PRD should be treated as a platform hardening umbrella, not a single
  merge request.

- Recommended vertical-slice decomposition after PRD approval:
  1. tenant ownership and authorization hardening
  2. structured audit framework + first coverage wave
  3. telemetry coverage expansion + admin dashboard completion
  4. ontology contract and relationship hardening
  5. cleaning engine and lineage depth improvements
  6. action API normalization

- The first slice should stay narrow and high-leverage:
  fix real tenant and permissions gaps before adding more ontology capability.

- Existing PRDs remain relevant:
  - entity mapping and relationship PRDs define current semantic config surfaces
  - schema drift PRD defines current dataset-health drift behavior
  - operational health dashboard PRD defines current telemetry rollup direction

- This hardening program should deepen those PRDs, not invalidate them.
