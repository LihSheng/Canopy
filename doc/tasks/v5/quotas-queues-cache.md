# Tenant Quotas, Queues, And Cache

## Goal

Add hard safety limits, warning thresholds, tenant-aware queue fairness, and
shared caching for routing and config metadata.

## Tasks

- [x] Add tenant-level quota records in the control plane.
- [x] Enforce hard limits for safety-critical operations.
- [x] Emit warnings for growth limits before hard failure.
- [x] Route jobs through tenant-aware queues with fairness controls.
- [x] Add concurrency caps per tenant.
- [x] Cache tenant routing metadata with a short TTL.
- [x] Cache tenant config and feature flags in the shared cache.
- [x] Invalidate cache on provisioning, suspension, config change, and DB
  rotation.

## Testing

- [x] Add unit tests for quota evaluation and warning thresholds.
- [x] Add integration tests for queue fairness and concurrency caps.
- [x] Add cache invalidation tests for lifecycle and config changes.

