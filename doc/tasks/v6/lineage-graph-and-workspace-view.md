# Lineage Graph And Workspace View

## Goal

Expose the path from source object to connection, dataset, version, and run inside the dataset workspace.

## Tasks

- [ ] Build the lineage graph from stored records.
- [ ] Include source object, connection, dataset, version, and run nodes.
- [ ] Render lineage inside the dataset workspace.
- [ ] Keep the lineage output understandable when part of the chain is missing.

## Testing

- [ ] Verify lineage graph generation from a successful import.
- [ ] Verify lineage remains stable after re-import.
- [ ] Verify missing-node fallback behavior.

