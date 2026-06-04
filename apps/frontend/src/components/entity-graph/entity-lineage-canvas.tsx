"use client";

import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { EntityLineageGraph, LineageNode, LineageEdge } from "@/lib/api/types";

type Props = {
  lineage: EntityLineageGraph;
  onNodeClick?: (node: Node) => void;
  onLayoutChange?: (layout: Record<string, { x: number; y: number }>) => void;
};

const KIND_STYLES: Record<string, { background: string; border: string }> = {
  entity: { background: "#fef3c7", border: "2px solid #f59e0b" },
  dataset: { background: "#f4f4f5", border: "1px solid #a1a1aa" },
  source: { background: "#dbeafe", border: "1px solid #3b82f6" },
  derived: { background: "#f3e8ff", border: "1px solid #a855f7" },
};

const EDGE_COLORS: Record<string, string> = {
  lineage: "#a1a1aa",
  binding: "#8b5cf6",
  link: "#3b82f6",
};

function resolvePosition(
  nodeId: string,
  defaultX: number,
  defaultY: number,
  layoutState: Record<string, { x: number; y: number }> | undefined
): { x: number; y: number } {
  if (layoutState?.[nodeId]) {
    return layoutState[nodeId];
  }
  return { x: defaultX, y: defaultY };
}

/** Compute a sensible default layout: entity center, upstream above, targets to the right. */
function computeDefaultLayout(
  lineage: EntityLineageGraph
): Record<string, { x: number; y: number }> {
  const layout: Record<string, { x: number; y: number }> = {};
  const entityIndex = lineage.nodes.findIndex((n) => n.id === "entity");
  if (entityIndex !== -1) {
    layout["entity"] = { x: 300, y: 400 };
  }

  const dsNode = lineage.nodes.find((n) => n.kind === "dataset");
  if (dsNode) {
    layout[dsNode.id] = { x: 300, y: 50 };
  }
  const dvNode = lineage.nodes.find(
    (n) => n.id === "dataset-version" || n.subtype === "dataset_version"
  );
  if (dvNode) {
    layout[dvNode.id] = { x: 300, y: 220 };
  }

  const sources = lineage.nodes.filter(
    (n) => n.kind === "source" || (n.kind === "derived" && n.subtype !== "dataset_version")
  );
  sources.forEach((sn, i) => {
    layout[sn.id] = { x: 50, y: 100 + i * 160 };
  });

  const targets = lineage.nodes.filter(
    (n) => n.kind === "entity" && n.id !== "entity"
  );
  targets.forEach((tn, i) => {
    layout[tn.id] = { x: 600, y: 300 + i * 160 };
  });

  return layout;
}

/**
 * Find the chain of derived nodes reachable from a start node via lineage edges.
 * Returns all derived node IDs in the chain (including the start node).
 * Stops at non-derived nodes.
 */
function findDerivedChain(
  startId: string,
  nodes: LineageNode[],
  edges: LineageEdge[]
): string[] {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  // Build adjacency: source_id → [target_ids]
  const adjacency = new Map<string, string[]>();
  for (const e of edges) {
    if (e.kind === "lineage") {
      const targets = adjacency.get(e.source_id) || [];
      targets.push(e.target_id);
      adjacency.set(e.source_id, targets);
    }
  }

  const chain: string[] = [];
  const visited = new Set<string>();
  const queue = [startId];

  while (queue.length > 0) {
    const current = queue.shift()!;
    if (visited.has(current)) continue;
    visited.add(current);

    const node = nodeMap.get(current);
    if (!node) continue;

    if (node.kind === "derived") {
      chain.push(current);
      // Follow outgoing lineage edges to more derived nodes
      const nextIds = adjacency.get(current) || [];
      for (const nextId of nextIds) {
        const next = nodeMap.get(nextId);
        if (next && next.kind === "derived" && !visited.has(nextId)) {
          queue.push(nextId);
        }
      }
    }
  }

  return chain;
}

function buildReactFlowGraph(
  lineage: EntityLineageGraph,
  collapsedIds: Set<string>
) {
  const defaultLayout = computeDefaultLayout(lineage);
  const layoutState = lineage.layout_state || {};

  // Determine which nodes to hide (collapsed)
  const hidden = new Set<string>();
  const chainSummaries: Map<string, { label: string; count: number; nodeIds: string[] }> =
    new Map();

  for (const collapsedId of collapsedIds) {
    const chain = findDerivedChain(collapsedId, lineage.nodes, lineage.edges);
    if (chain.length > 0) {
      // Last node in the chain is the "visible" label
      const lastNode = lineage.nodes.find((n) => n.id === chain[chain.length - 1]);
      const lastLabel = lastNode?.label || chain[chain.length - 1];
      const hiddenCount = chain.length - 1; // all except the last
      chainSummaries.set(collapsedId, {
        label: lastLabel,
        count: hiddenCount,
        nodeIds: chain,
      });
      // Hide all except the last
      for (let i = 0; i < chain.length - 1; i++) {
        hidden.add(chain[i]);
      }
    }
  }

  const nodes: Node[] = [];
  for (const ln of lineage.nodes) {
    if (hidden.has(ln.id)) continue;

    const style = KIND_STYLES[ln.kind] || {
      background: "#fff",
      border: "1px solid #e4e4e7",
    };
    const pos = resolvePosition(
      ln.id,
      defaultLayout[ln.id]?.x || 100,
      defaultLayout[ln.id]?.y || 100,
      layoutState
    );

    // Build display label
    let label = ln.label;
    let isCollapsedSummary = false;
    let collapsedHiddenCount = 0;

    // Check if this node is a chain summary
    for (const [chainStart, summary] of chainSummaries) {
      if (summary.nodeIds.includes(ln.id)) {
        // Is this the last node in the chain (the visible one)?
        const lastInChain = summary.nodeIds[summary.nodeIds.length - 1];
        if (ln.id === lastInChain && summary.count > 0) {
          label = `${summary.label} (+${summary.count} hidden)`;
          isCollapsedSummary = true;
          collapsedHiddenCount = summary.count;
        }
      }
    }

    if (ln.kind === "entity" && ln.properties.length > 0 && !isCollapsedSummary) {
      label = `${ln.label}\n[${ln.properties.join(", ")}]`;
    }

    nodes.push({
      id: ln.id,
      type: "default",
      position: pos,
      data: {
        label,
        nodeType: ln.kind,
        subtype: ln.subtype || undefined,
        properties: ln.properties,
        collapsed: isCollapsedSummary || collapsedIds.has(ln.id),
        collapsedCount: collapsedHiddenCount || ln.collapsed_count,
      },
      style: {
        padding: "10px 16px",
        borderRadius: "8px",
        fontSize: "13px",
        fontWeight: 500,
        whiteSpace: "pre-wrap" as const,
        textAlign: "center" as const,
        ...style,
        ...(isCollapsedSummary ? { borderStyle: "dashed" } : {}),
      },
    });
  }

  // Filter edges — hide edges connecting to hidden nodes
  const edgeSet = new Set(hidden);
  const edges: Edge[] = lineage.edges
    .filter((le) => !edgeSet.has(le.source_id) && !edgeSet.has(le.target_id))
    .map((le) => ({
      id: le.id,
      source: le.source_id,
      target: le.target_id,
      sourceHandle: le.source_handle || undefined,
      targetHandle: le.target_handle || undefined,
      label: le.label || undefined,
      style: {
        stroke: EDGE_COLORS[le.kind] || "#a1a1aa",
        strokeDasharray:
          le.kind === "binding" ? "3 3" : le.kind === "link" ? "5 5" : undefined,
      },
    }));

  return { nodes, edges };
}

export const EntityLineageCanvas = ({ lineage, onNodeClick, onLayoutChange }: Props) => {
  const [collapsedIds, setCollapsedIds] = useState<Set<string>>(new Set());

  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => buildReactFlowGraph(lineage, collapsedIds),
    [lineage, collapsedIds]
  );
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const nodeData = node.data as {
        nodeType?: string;
        subtype?: string;
      };

      // Collapse toggle for derived nodes only (exclude dataset-version)
      if (
        nodeData.nodeType === "derived" &&
        nodeData.subtype !== "dataset_version"
      ) {
        setCollapsedIds((prev) => {
          const next = new Set(prev);
          if (next.has(node.id)) {
            next.delete(node.id);
          } else {
            next.add(node.id);
          }
          return next;
        });
        return; // Don't propagate to parent onNodeClick for collapse toggle
      }

      onNodeClick?.(node);
    },
    [onNodeClick]
  );

  const handleNodesChange = (changes: unknown[]) => {
    onNodesChange(changes as Parameters<typeof onNodesChange>[0]);

    if (onLayoutChange) {
      const layout: Record<string, { x: number; y: number }> = {};
      const typedChanges = changes as Array<{
        id?: string;
        position?: { x: number; y: number };
        type?: string;
      }>;
      const positionChanges: Record<string, { x: number; y: number }> = {};
      typedChanges.forEach((ch) => {
        if (ch.id && ch.position && ch.type === "position") {
          positionChanges[ch.id] = ch.position;
        }
      });

      nodes.forEach((n) => {
        const pos = positionChanges[n.id] || n.position;
        layout[n.id] = { x: pos.x, y: pos.y };
      });

      onLayoutChange(layout);
    }
  };

  return (
    <ReactFlowProvider>
      <div style={{ height: 500, width: "100%" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={handleNodeClick}
          onNodesChange={handleNodesChange}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
};
