# V5 Ontology TODO

## Purpose

This note tracks ontology-related decisions that are intentionally deferred
from the v5 database architecture.

## Deferred topics

- tenant-configurable ontology object types
- ontology field modeling
- hybrid JSONB versus normalized custom property structures
- publish-time ontology validation rules
- ontology-specific access control
- ontology storage split between clean data and business objects

## Rule

Do not let ontology decisions leak back into the v5 database design until the
platform and tenant database foundation is finalized.

