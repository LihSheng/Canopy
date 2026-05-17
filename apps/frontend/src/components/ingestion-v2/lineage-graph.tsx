"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchLineage, type LineageEdge, type LineageGraphResult, type LineageNode } from "@/lib/api/ingestion";
import { ErrorState } from "@/components/shared/error-state";

type Props = {
  uploadId: string;
};

const NODE_COLORS: Record<string, string> = {
  file: "border-blue-400 bg-blue-50 text-blue-800",
  sheet: "border-teal-400 bg-teal-50 text-teal-800",
  raw_column: "border-amber-400 bg-amber-50 text-amber-800",
  cleaned_field: "border-emerald-400 bg-emerald-50 text-emerald-800",
  ontology_field: "border-violet-400 bg-violet-50 text-violet-800",
};

const NODE_LABELS: Record<string, string> = {
  file: "File",
  sheet: "Sheet",
  raw_column: "Raw Column",
  cleaned_field: "Cleaned Field",
  ontology_field: "Ontology Field",
};

const LAYER_ORDER = ["file", "sheet", "raw_column", "cleaned_field", "ontology_field"];

export function LineageGraph({ uploadId }: Props) {
  const [data, setData] = useState<LineageGraphResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchLineage(uploadId)
      .then((result) => { if (!cancelled) setData(result); })
      .catch((err) => { if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load lineage"); });
    return () => { cancelled = true; };
  }, [uploadId]);

  const getConnectedNodeIds = useCallback(
    (nodeId: string): Set<string> => {
      if (!data) return new Set();
      const connected = new Set<string>([nodeId]);
      for (const edge of data.edges) {
        if (edge.from_node_id === nodeId) connected.add(edge.to_node_id);
        if (edge.to_node_id === nodeId) connected.add(edge.from_node_id);
      }
      return connected;
    },
    [data],
  );

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center py-12">
        <svg className="h-6 w-6 animate-spin text-zinc-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (data.nodes.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 p-8 text-center text-sm text-zinc-400">
        No lineage data available for this upload.
      </div>
    );
  }

  const layers = LAYER_ORDER
    .map((layerType) => ({
      type: layerType,
      label: NODE_LABELS[layerType] || layerType,
      nodes: data.nodes.filter((n) => n.node_type === layerType),
    }))
    .filter((layer) => layer.nodes.length > 0);

  const connectedIds = hoveredNodeId ? getConnectedNodeIds(hoveredNodeId) : null;

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-6">
        {layers.map((layer) => (
          <div key={layer.type}>
            <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              {layer.label}
            </div>
            <div className="flex flex-wrap gap-2">
              {layer.nodes.map((node) => {
                const isDimmed = connectedIds !== null && !connectedIds.has(node.id);
                const isSelected = selectedNode?.id === node.id;
                return (
                  <button
                    key={node.id}
                    type="button"
                    onMouseEnter={() => setHoveredNodeId(node.id)}
                    onMouseLeave={() => setHoveredNodeId(null)}
                    onClick={() => setSelectedNode(isSelected ? null : node)}
                    className={`rounded-lg border-2 px-3 py-1.5 text-left text-sm transition-all ${
                      NODE_COLORS[node.node_type] || "border-zinc-300 bg-white text-zinc-700"
                    } ${
                      isDimmed ? "opacity-30" : "opacity-100"
                    } ${
                      isSelected ? "ring-2 ring-zinc-900" : ""
                    }`}
                  >
                    <span className="font-medium">{node.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {selectedNode && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm">
          <div className="mb-2 flex items-center gap-2">
            <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${
              NODE_COLORS[selectedNode.node_type] || "border-zinc-300 bg-white text-zinc-700"
            }`}>
              {NODE_LABELS[selectedNode.node_type] || selectedNode.node_type}
            </span>
            <span className="font-medium text-zinc-900">{selectedNode.label}</span>
          </div>
          {selectedNode.metadata && Object.keys(selectedNode.metadata).length > 0 && (
            <div className="mt-2 space-y-1 text-xs text-zinc-600">
              {Object.entries(selectedNode.metadata).map(([key, value]) => (
                <div key={key}>
                  <span className="font-semibold text-zinc-700">{key}: </span>
                  <span>{JSON.stringify(value, null, 1)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
