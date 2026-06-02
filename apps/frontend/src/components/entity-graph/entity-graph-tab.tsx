"use client";

import { useCallback, useEffect, useState } from "react";
import type { Node } from "@xyflow/react";
import {
  fetchMapping,
  fetchObjectTypes,
  createObjectType,
  fetchDatasetVersionSchema,
  createMapping,
} from "@/lib/api/semantic";
import type {
  ComputedProperty,
  Dataset,
  DatasetVersion,
  EntityLink,
  ObjectType,
  PropertyMapping,
  SchemaColumn,
  SemanticMapping,
  SourceNode,
} from "@/lib/api/types";
import { LoadingSpinner, useToast } from "@/components/shared";
import { EntityGraphCanvas } from "./entity-graph-canvas";
import { SourceRegistrationDrawer } from "./source-registration-drawer";
import { NodeEditDrawer, type SelectedNode } from "./node-edit-drawer";

type Props = {
  dataset: Dataset;
  versions: DatasetVersion[];
};

export const EntityGraphTab = ({ dataset, versions }: Props) => {
  const [loading, setLoading] = useState(true);
  const [mapping, setMapping] = useState<SemanticMapping | null>(null);
  const [showSourceDrawer, setShowSourceDrawer] = useState(false);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [layoutState, setLayoutState] = useState<Record<string, { x: number; y: number }>>({});
  const [saving, setSaving] = useState(false);
  const toast = useToast();

  // ─── Inline object-type creation (canvas-native, replaces wizard) ───
  const [objectTypes, setObjectTypes] = useState<ObjectType[]>([]);
  const [schemaColumns, setSchemaColumns] = useState<SchemaColumn[]>([]);
  const [selectedObjectTypeId, setSelectedObjectTypeId] = useState<string>("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTypeKey, setNewTypeKey] = useState("");
  const [newTypeDisplayName, setNewTypeDisplayName] = useState("");
  const [newTypeDescription, setNewTypeDescription] = useState("");
  const [creatingType, setCreatingType] = useState(false);
  const [creatingMapping, setCreatingMapping] = useState(false);

  const activeVersion = versions.find(
    (v) => v.id === dataset.active_version_id
  );

  // Update mapping locally when sources change
  const updateMappingSources = useCallback(
    (sourceNodes: SourceNode[]) => {
      setMapping((prev) => (prev ? { ...prev, source_nodes: sourceNodes } : prev));
    },
    []
  );

  // Load schema + object types for inline creation when no mapping exists
  const loadInlineData = useCallback(async () => {
    if (!activeVersion) return;
    try {
      const [types, schema] = await Promise.all([
        fetchObjectTypes(),
        fetchDatasetVersionSchema(dataset.id, activeVersion.id),
      ]);
      setObjectTypes(types);
      setSchemaColumns(schema);
    } catch {
      // non-fatal — user can still create object type manually
    }
  }, [dataset.id, activeVersion]);

  /* eslint-disable react-hooks/set-state-in-effect -- initial load */
  useEffect(() => {
    if (!mapping && activeVersion) {
      loadInlineData();
    }
  }, [mapping, activeVersion, loadInlineData]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const getDefaultSemanticType = (primitiveType?: string | null) => {
    switch (primitiveType) {
      case "integer":
      case "number":
      case "boolean":
      case "datetime":
      case "date":
      case "string":
        return primitiveType;
      default:
        return "string";
    }
  };

  const load = useCallback(async () => {
    if (!activeVersion) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const m = await fetchMapping(dataset.id, activeVersion.id);
      setMapping(m);
    } catch {
      // mapping stays null
    } finally {
      setLoading(false);
    }
  }, [dataset.id, activeVersion]);

  /* eslint-disable react-hooks/set-state-in-effect -- initial load */
  useEffect(() => {
    load();
  }, [load]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const handleCreateObjectType = async () => {
    if (!newTypeKey || !newTypeDisplayName) return;
    setCreatingType(true);
    try {
      const newType = await createObjectType({
        object_type_key: newTypeKey,
        display_name: newTypeDisplayName,
        description: newTypeDescription,
      });
      setObjectTypes((prev) => [newType, ...prev]);
      setSelectedObjectTypeId(newType.id);
      setShowCreateForm(false);
      setNewTypeKey("");
      setNewTypeDisplayName("");
      setNewTypeDescription("");
      toast.success("Object type created", `"${newType.display_name}" created.`);
    } catch (err) {
      toast.danger(
        "Failed to create",
        err instanceof Error ? err.message : "Unknown error"
      );
    } finally {
      setCreatingType(false);
    }
  };

  const handleCreateMapping = async () => {
    if (!selectedObjectTypeId || !activeVersion) return;
    setCreatingMapping(true);
    try {
      // Auto-initialize properties from schema columns (all included, no PK yet)
      const schema = schemaColumns.length > 0
        ? schemaColumns
        : await fetchDatasetVersionSchema(dataset.id, activeVersion.id);
      const initialProperties: PropertyMapping[] = schema.map((col) => ({
        source_column: col.column_name,
        property_name: col.column_name,
        semantic_type: getDefaultSemanticType(col.primitive_type),
        included: true,
        is_primary_key: false,
      }));
      const result = await createMapping(dataset.id, activeVersion.id, {
        object_type_id: selectedObjectTypeId,
        properties: initialProperties,
        source_nodes: mapping?.source_nodes,
        layout_state: layoutState,
      });
      setMapping(result);
      toast.success("Mapping created", `Entity mapping published as v${result.version_number}.`);
    } catch (err) {
      toast.danger(
        "Save failed",
        err instanceof Error ? err.message : "Unknown error"
      );
    } finally {
      setCreatingMapping(false);
    }
  };

  const handleUpdateLinks = (updatedLinks: EntityLink[]) => {
    setMapping((prev) =>
      prev ? { ...prev, links: updatedLinks } : prev
    );
  };

  const handleAddSource = (node: SourceNode) => {
    const updated = [...(mapping?.source_nodes || []), node];
    updateMappingSources(updated);
    toast.success("Source added", `"${node.name}" registered as a source node.`);
  };

  const handleRemoveSource = (sourceId: string) => {
    const updated = (mapping?.source_nodes || []).filter((sn) => sn.source_id !== sourceId);
    updateMappingSources(updated);
    toast.info("Source removed", "Source node removed from graph.");
  };

  const handleNodeClick = (node: Node) => {
    setSelectedNode(node as unknown as SelectedNode);
    setShowSourceDrawer(false);
  };

  const handleUpdateProperties = (properties: PropertyMapping[]) => {
    setMapping((prev) =>
      prev ? { ...prev, properties } : prev
    );
  };

  const handleUpdateComputedProperties = (computedProperties: ComputedProperty[]) => {
    setMapping((prev) =>
      prev ? { ...prev, computed_properties: computedProperties } : prev
    );
  };

  const handleLayoutChange = (layout: Record<string, { x: number; y: number }>) => {
    setLayoutState(layout);
  };

  const handleSave = async () => {
    if (!mapping || !activeVersion) return;
    setSaving(true);
    try {
      const { updateMapping } = await import("@/lib/api/semantic");
      const result = await updateMapping(dataset.id, activeVersion.id, {
        object_type_id: mapping.object_type_id,
        properties: mapping.properties,
        links: mapping.links,
        source_nodes: mapping.source_nodes,
        computed_properties: mapping.computed_properties,
        layout_state: layoutState,
      });
      setMapping(result);
      toast.success("Saved", `Graph saved as v${result.version_number}.`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to save graph";
      toast.danger("Save failed", message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading entity graph..." />;
  }

  // No active version — cannot create mapping
  if (!activeVersion) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-zinc-100 p-4">
          <svg
            className="size-8 text-zinc-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
            />
          </svg>
        </div>
        <p className="text-base font-medium text-zinc-900">
          No active dataset version
        </p>
        <p className="mt-1 max-w-sm text-sm text-zinc-500">
          Refresh the dataset to create an active version, or import data first.
        </p>
      </div>
    );
  }

  // No mapping yet — show canvas-native inline creation panel
  if (!mapping) {
    const selectedType = objectTypes.find((t) => t.id === selectedObjectTypeId);
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 rounded-full bg-zinc-100 p-4">
          <svg
            className="size-8 text-zinc-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
            />
          </svg>
        </div>
        <p className="text-base font-medium text-zinc-900">
          No entity mapping yet
        </p>
        <p className="mt-1 max-w-sm text-sm text-zinc-500">
          Map dataset columns to a reusable Object Type with primary key and
          friendly property names for use in dashboards and exports.
        </p>

        <div className="mt-6 w-full max-w-md space-y-4 rounded-lg border border-zinc-200 bg-white p-5 text-left">
          <h3 className="text-sm font-semibold text-zinc-900">
            Create Entity Mapping
          </h3>

          {/* Select existing object type */}
          {objectTypes.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-zinc-600 mb-1">
                Object Type
              </label>
              <select
                value={selectedObjectTypeId}
                onChange={(e) => setSelectedObjectTypeId(e.target.value)}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              >
                <option value="">-- Select object type --</option>
                {objectTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.display_name} ({t.object_type_key})
                  </option>
                ))}
              </select>
              {selectedType && (
                <p className="mt-1 text-xs text-zinc-400">
                  Key: {selectedType.object_type_key}
                </p>
              )}
            </div>
          )}

          {objectTypes.length === 0 && !showCreateForm && (
            <p className="text-xs text-zinc-400">
              No object types exist yet. Create one below.
            </p>
          )}

          {/* Create new object type inline */}
          {!showCreateForm ? (
            <button
              type="button"
              onClick={() => setShowCreateForm(true)}
              className="text-xs font-medium text-zinc-600 hover:text-zinc-900"
            >
              + Create new Object Type
            </button>
          ) : (
            <div className="space-y-3 rounded-md border border-zinc-200 bg-zinc-50 p-4">
              <h4 className="text-xs font-semibold text-zinc-700">
                New Object Type
              </h4>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Key (lowercase_snake, immutable)
                </label>
                <input
                  type="text"
                  value={newTypeKey}
                  onChange={(e) =>
                    setNewTypeKey(
                      e.target.value
                        .toLowerCase()
                        .replace(/[^a-z0-9_]/g, "_")
                    )
                  }
                  placeholder="e.g. employee"
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={newTypeDisplayName}
                  onChange={(e) => setNewTypeDisplayName(e.target.value)}
                  placeholder="e.g. Employee"
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Description (optional)
                </label>
                <input
                  type="text"
                  value={newTypeDescription}
                  onChange={(e) => setNewTypeDescription(e.target.value)}
                  placeholder="Brief description..."
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleCreateObjectType}
                  disabled={creatingType || !newTypeKey || !newTypeDisplayName}
                  className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {creatingType ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Confirm mapping creation */}
          <button
            type="button"
            onClick={handleCreateMapping}
            disabled={!selectedObjectTypeId || creatingMapping}
            className="w-full rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {creatingMapping
              ? "Creating mapping..."
              : selectedObjectTypeId
                ? `Configure "${selectedType?.display_name ?? selectedObjectTypeId}" Mapping`
                : "Select an Object Type to continue"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">
            Entity: <span className="font-medium text-zinc-900">{mapping.object_type_key}</span>
          </span>
          <span className="text-xs text-zinc-400">v{mapping.version_number}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowSourceDrawer(true)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            + Add Source
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      <EntityGraphCanvas
        dataset={dataset}
        mapping={mapping}
        onNodeClick={handleNodeClick}
        onLayoutChange={handleLayoutChange}
      />

      {selectedNode && (
        <NodeEditDrawer
          node={selectedNode}
          sourceNodes={mapping.source_nodes?.map((sn) => ({
            source_id: sn.source_id,
            name: sn.name,
            source_type: sn.source_type,
            fields: sn.fields || [],
          }))}
          onClose={() => setSelectedNode(null)}
          onUpdateProperties={handleUpdateProperties}
          onUpdateComputedProperties={handleUpdateComputedProperties}
          links={mapping.links}
          onUpdateLinks={handleUpdateLinks}
          objectTypes={objectTypes}
        />
      )}

      {selectedNode && (
        <div
          className="fixed inset-0 z-30 bg-black/20"
          onClick={() => setSelectedNode(null)}
        />
      )}

      {showSourceDrawer && (
        <SourceRegistrationDrawer
          projectId={dataset.project_id}
          datasetId={dataset.id}
          sourceNodes={mapping.source_nodes || []}
          onAdd={handleAddSource}
          onRemove={handleRemoveSource}
          onClose={() => setShowSourceDrawer(false)}
        />
      )}

      {showSourceDrawer && (
        <div
          className="fixed inset-0 z-30 bg-black/20"
          onClick={() => setShowSourceDrawer(false)}
        />
      )}
    </div>
  );
};
