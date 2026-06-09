# PRD: Phase 7 Universal Connector Framework

Status: draft

## Problem Statement

Canopy has outgrown its narrow source-ingestion boundary.

Today the platform can read from a small set of hardcoded source types, but it
does not yet have a single connector model that can:

- discover and normalize data from different source classes through one
  contract
- store connector configuration, credentials, policies, and health state in one
  tenant-aware registry
- drive a consistent UI flow for adding connections, testing them, previewing
  schemas, and configuring sync
- support explicit connector actions with policy checks, audit trails, and
  idempotency
- distinguish safe, approved actions from uncontrolled side effects
- expose connector health, retries, and failure history in a way operators can
  trust

Without that framework, every new source type becomes a one-off integration.
That creates repeated work in the backend, the UI, policy enforcement, audit
logging, and job orchestration. It also makes it impossible to build a broader
platform on top of connectors because later phases need a stable source and
action boundary.

The product problem is not just “add more connectors.” The problem is to define
one reusable connector system that can support:

- read operations for discovery, preview, batch sync, and streaming where
  applicable
- explicit, audited actions for approved connected systems
- tenant-scoped storage of connector configuration and credentials
- a coherent operator experience for setup, sync policy, health, and history

## Solution

Build a Universal Connector Framework as the source-access foundation for the
platform.

The framework will provide:

- a connector base contract for connecting, discovering schema, reading data,
  executing approved actions, checking health, and closing resources
- a connector registry that stores type, configuration, encrypted credentials,
  action scope, tenant scope, and operational metadata
- a connector wizard UI for connection setup, test, schema preview, and sync
  configuration
- a sync policy engine for schedules, manual runs, incremental sync support,
  and policy enforcement
- connector health monitoring for status, latency, retries, and failure
  tracking
- a connector action model that supports explicit actions with validation,
  idempotency, audit logging, and approval gates

Phase 7 should land in vertical slices:

1. Connector contract and policy model
2. Read-path foundation
3. Create and update actions
4. Approval workflow
5. Delete actions
6. Webhook-triggered actions

The first usable release should ship the read path plus create/update actions.
The later action types should reuse the same connector contract rather than
introducing separate systems.

The product outcome should be:

- a user can add a connector, test it, and preview discovered schema
- a user can configure sync policy and see data land on schedule
- a user can run approved create/update actions where the target supports them
- an operator can inspect health and failure history per connector
- a security model can restrict risky actions like delete to explicit policy
- the platform keeps a single source and action model for future phases

## User Stories

1. As a data engineer, I want to add a new connector from a single wizard, so
   that I do not have to stitch together connection setup across multiple
   screens.

2. As a data engineer, I want to test a connector before saving it, so that I
   can catch bad credentials or network issues early.

3. As a data engineer, I want to see discovered schemas before sync starts, so
   that I can confirm the connector sees the right source objects.

4. As a data engineer, I want to name and label a connector, so that I can
   recognize it later in the registry.

5. As a data engineer, I want credentials to be encrypted at rest, so that
   connection secrets are not exposed in storage or logs.

6. As a tenant admin, I want each connector to be tenant-scoped, so that one
   tenant cannot see or use another tenant's connector configuration.

7. As a tenant admin, I want connector types and configuration to be stored in a
   registry, so that the platform has one source of truth for connector state.

8. As a tenant admin, I want connector health to be visible, so that I can tell
   whether the connector is healthy, degraded, or failing.

9. As a data engineer, I want to configure a sync schedule per connector, so
   that each source can refresh on its own cadence.

10. As a data engineer, I want to run a sync manually, so that I can refresh
    data on demand when a source changes unexpectedly.

11. As a data engineer, I want to configure incremental sync support where the
    source allows it, so that large sources do not need full re-pulls every
    time.

12. As a data engineer, I want sync history to be recorded, so that I can
    inspect when a source last ran and whether it succeeded.

13. As an operator, I want retry behavior to be explicit and visible, so that I
    know whether a failure is transient or persistent.

14. As an operator, I want connector failures to show structured error detail,
    so that I can diagnose connection, auth, schema, and execution failures
    quickly.

15. As a platform user, I want connector schema discovery to support JDBC,
    REST, and file sources, so that the framework is not locked to one source
    family.

16. As a data engineer, I want the connector contract to expose read and action
    operations in one interface, so that later capabilities reuse the same
    framework.

17. As a data engineer, I want to execute approved create actions through a
    connector, so that I can create records in a connected system when the
    target supports it.

18. As a data engineer, I want to execute approved update actions through a
    connector, so that I can change records in a connected system when the
    target supports it.

19. As a security reviewer, I want every action to require an explicit policy
    scope, so that the platform cannot perform arbitrary writes.

20. As a security reviewer, I want every action to be idempotent, so that
    retries do not create duplicate side effects.

21. As an auditor, I want each action attempt to be logged with request,
    outcome, and actor metadata, so that I can reconstruct what happened later.

22. As an approver, I want risky actions to pause for approval, so that humans
    can review the change before it executes.

23. As an approver, I want to approve or reject a pending action, so that the
    system respects a human control point.

24. As a tenant admin, I want delete actions to require stricter policy than
    create or update, so that destructive behavior is not exposed casually.

25. As a tenant admin, I want delete actions to support a clear recovery story,
    so that accidental destructive operations can be undone or mitigated.

26. As an operator, I want webhook-triggered actions to verify signatures and
    deduplicate events, so that external callbacks do not create repeated
    execution.

27. As an operator, I want webhook-triggered actions to retry delivery safely,
    so that temporary outages do not silently lose events.

28. As a product manager, I want the connector framework to support more than
    one source family, so that the platform can grow without rewriting its
    foundation.

29. As a platform architect, I want one stable connector contract for all
    action types, so that later phases do not need separate execution models.

30. As a platform architect, I want connector behavior to remain tenant-aware
    and snapshot-aware, so that data and actions do not break product isolation
    guarantees.

31. As a data engineer, I want schema preview, sync, and actions to live in one
    consistent flow, so that I can understand the connector before using it
    operationally.

32. As a support engineer, I want connector events and health history to be
    queryable, so that I can troubleshoot customer issues without guessing.

33. As a platform user, I want the connector UI to make the difference between
    read-only operations and action operations obvious, so that I do not
    accidentally run a destructive operation.

34. As a platform user, I want connector policies to be editable without
    rewriting connector code, so that policy changes do not require a code
    release.

35. As a platform user, I want later action types to reuse the same connector
    surface, so that the product grows in a predictable way.

## Implementation Decisions

- Build a single connector domain that owns connection setup, schema
  discovery, sync execution, action execution, health, and lifecycle control.
- Keep the connector registry tenant-aware and store type, config, encrypted
  credentials, action scope, and operational state together.
- Represent connector actions with one stable contract that includes action
  type, input schema, permission scope, idempotency key, audit metadata, and
  result state.
- Treat create and update as the first shipped action types.
- Treat approval, delete, and webhook-triggered actions as later slices of the
  same framework, not separate framework implementations.
- Make policy checks explicit and connector-scoped so that only approved action
  types can execute.
- Keep connector reads and connector actions separated at the execution level
  but shared at the contract level.
- Use the connector wizard as the user-facing entrypoint for add, test,
  preview, sync, and action configuration.
- Persist sync history and health history so operators can inspect recent and
  historical failures.
- Keep source-specific logic inside connector adapters and mappers, not in the
  generic orchestration layer.
- Preserve snapshot-scoped behavior for downstream analytics and AI, even while
  connectors gain action support.
- Stage the delivery in vertical slices rather than building every action type
  before any user-facing value ships.

## Testing Decisions

- Good tests verify external behavior: connection setup, schema discovery,
  sync scheduling, action execution, approval gating, health reporting, and
  audit visibility.
- Test the connector contract through service-level and API-level behavior,
  not by asserting private implementation details.
- Test the wizard flow end to end with mocked connector backends and real
  request/response contracts.
- Test the registry and policy engine as persistence-plus-domain behavior, not
  as raw ORM behavior.
- Test action execution with explicit success, failure, retry, duplicate
  request, and approval-pending cases.
- Test webhook-triggered behavior for signature validation, dedupe, and retry
  behavior.
- Prior art in the repo includes connection wizard tests, sync policy tests,
  refresh orchestration tests, and other API/service split tests that already
  exercise behavior through stable seams.
- Preferred seams are the connector service, registry service, policy engine,
  approval state handler, and API routes for wizard and operational actions.

## Out of Scope

- Dynamic ontology modeling
- Analytics aggregation beyond connector-side discovery and sync output
- Dashboard widgets and application builder work
- AI chat, semantic search, and AI-generated dashboards
- Full automation engine and observability platform work beyond connector
  health and history
- Distributed compute, microservice decomposition, and warehouse-scale
  orchestration
- Uncontrolled writeback paths or ad hoc mutations outside approved connector
  actions
- Real-time CDC implementation for the first phase of connector work
- Exotic connector coverage for every vendor on day one
- Any action path that bypasses policy checks, audit logging, or idempotency

## Further Notes

- This PRD is the umbrella requirement for Phase 7 and should be broken into
  vertical slices in implementation order.
- The recommended execution order is contract and policy model, read path,
  create/update actions, approvals, delete, then webhook-triggered actions.
- The product should ship value after the read path and create/update slice
  instead of waiting for every action type to be complete.
- The architecture now allows explicit, audited actions, but the framework must
  still protect users from uncontrolled side effects.
- The PRD assumes the platform remains tenant-aware and snapshot-consistent
  even as connector scope expands.
