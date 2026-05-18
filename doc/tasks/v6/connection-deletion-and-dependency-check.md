# Connection Deletion And Dependency Check

## Goal

Allow deletion of an unused app-owned connection record and block deletion when active downstream dependencies still exist.

## Tasks

- [ ] Expose a dependency summary for a connection.
- [ ] Use the dependency summary to decide whether delete is allowed.
- [ ] Allow deletion when the connection has no active downstream usage.
- [ ] Block deletion when active datasets, runs, or modeled downstream assets still depend on the connection.
- [ ] Keep deletion scoped to the HERD Aggregator record, not the upstream source system.

## Testing

- [ ] Verify delete is blocked when dependencies exist.
- [ ] Verify delete succeeds when the connection is unused.
- [ ] Verify the UI can show the delete state from the dependency summary.

