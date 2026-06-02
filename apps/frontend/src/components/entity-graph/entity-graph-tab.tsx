"use client";

import { useCallback, useEffect, useState } from "react";
import type { Node } from "@xyflow/react";
import { fetchMapping } from "@/lib/api/semantic";
import type { ComputedProperty, Dataset, DatasetVersion, PropertyMapping, SemanticMapping, SourceNode } from "@/lib/api/types";
import { LoadingSpinner, useToast } from "@/components/shared";
import { EntityMappingWizard } from "@/components/entity-mapping/entity-mapping-wizard";
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
  const [showWizard, setShowWizard] = useState(false);
  const [showSourceDrawer, setShowSourceDrawer] = useState(false);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);
  const [layoutState, setLayoutState] = useState<Record<string, { x: number; y: number }>>({});
  const [saving, setSaving] = useState(false);
  const toast = useToast();

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

  const handleWizardComplete = () => {
    setShowWizard(false);
    load();
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
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

  // Wizard open for initial creation or editing
  if (showWizard) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h3 className="mb-4 text-sm font-semibold text-zinc-900">
          Configure Entity Mapping
        </h3>
        <EntityMappingWizard
          datasetId={dataset.id}
          datasetVersionId={activeVersion!.id}
          existingMapping={mapping}
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
        />
      </div>
    );
  }

  if (!mapping) {
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
        <button
          type="button"
          onClick={() => setShowWizard(true)}
          className="mt-6 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
        >
          Configure Entity Mapping
        </button>
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
            onClick={() => setShowWizard(true)}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Edit Mapping
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
