"use client";

import { useMemo } from "react";
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
import type { Dataset, SemanticMapping } from "@/lib/api/types";

type Props = {
  dataset: Dataset;
  mapping: SemanticMapping;
  onNodeClick?: (node: Node) => void;
  onLayoutChange?: (layout: Record<string, { x: number; y: number }>) => void;
};

const nodeBaseStyle = {
  padding: "10px 16px",
  borderRadius: "8px",
  border: "1px solid #e4e4e7",
  background: "#fff",
  fontSize: "13px",
  fontWeight: 500,
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

function buildGraph(
  dataset: Dataset,
  mapping: SemanticMapping,
  layoutState?: Record<string, { x: number; y: number }>
) {
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  const pos = (id: string, dx: number, dy: number) =>
    resolvePosition(id, dx, dy, layoutState);

  // Source lineage node (raw source)
  nodes.push({
    id: "source",
    type: "default",
    position: pos("source", 100, 100),
    data: { label: dataset.source_object_name, nodeType: "source", sourceType: "raw_input" },
    style: { ...nodeBaseStyle, background: "#f4f4f5", border: "1px dashed #a1a1aa" },
  });

  // Dataset node
  nodes.push({
    id: "dataset",
    type: "default",
    position: pos("dataset", 100, 250),
    data: { label: dataset.name, nodeType: "dataset" },
    style: nodeBaseStyle,
  });

  edges.push({
    id: "source-dataset",
    source: "source",
    target: "dataset",
    style: { stroke: "#a1a1aa" },
  });

  // Entity node
  nodes.push({
    id: "entity",
    type: "default",
    position: pos("entity", 100, 450),
    data: {
      label: mapping.object_type_key,
      nodeType: "entity",
      properties: mapping.properties || [],
    },
    style: {
      ...nodeBaseStyle,
      background: "#fef3c7",
      border: "2px solid #f59e0b",
    },
  });

  edges.push({
    id: "dataset-entity",
    source: "dataset",
    target: "entity",
    style: { stroke: "#f59e0b" },
  });

  // Collect all source node fields for field-to-property edge matching
  const sourceFields: Record<string, string> = {}; // source_column -> field name
  let sourceX = -200;
  (mapping.source_nodes || []).forEach((sn) => {
    const sourceId = `source-node-${sn.source_id}`;
    nodes.push({
      id: sourceId,
      type: "default",
      position: pos(sourceId, sourceX, 450),
      data: {
        label: sn.name,
        nodeType: "source",
        sourceType: sn.source_type,
        fields: sn.fields || [],
      },
      style: { ...nodeBaseStyle, background: "#dbeafe", border: "1px solid #3b82f6" },
    });

    edges.push({
      id: `${sourceId}-entity`,
      source: sourceId,
      target: "entity",
      style: { stroke: "#3b82f6" },
    });

    // Register fields for property matching
    (sn.fields || []).forEach((field) => {
      sourceFields[field] = sn.name;
    });

    sourceX -= 200;
  });

  // Source-field-to-property edges: connect source node to entity for each matched property
  const properties = mapping.properties || [];
  (mapping.source_nodes || []).forEach((sn) => {
    const sourceId = `source-node-${sn.source_id}`;
    properties.forEach((prop) => {
      if ((sn.fields || []).includes(prop.source_column)) {
        edges.push({
          id: `${sourceId}-field-${prop.source_column}`,
          source: sourceId,
          target: "entity",
          sourceHandle: prop.source_column,
          targetHandle: prop.property_name,
          label: prop.source_column,
          style: { stroke: "#8b5cf6", strokeWidth: 1, strokeDasharray: "3 3" },
        });
      }
    });
  });

  // Target reference nodes from links (PRD: "target references" for linked Object Types)
  let targetX = 400;
  (mapping.links || []).forEach((link) => {
    const targetId = `target-${link.target_object_type_id}`;
    nodes.push({
      id: targetId,
      type: "default",
      position: pos(targetId, targetX, 450),
      data: {
        label: link.display_name || link.target_object_type_id,
        nodeType: "target",
        linkInfo: {
          link_id: link.link_id,
          source_property_key: link.source_property_key,
          target_property_key: link.target_property_key,
          cardinality: link.cardinality,
        },
      },
      style: { ...nodeBaseStyle, border: "1px solid #3b82f6" },
    });

    edges.push({
      id: `entity-${link.target_object_type_id}`,
      source: "entity",
      target: targetId,
      style: { stroke: "#3b82f6", strokeDasharray: "5 5" },
    });

    targetX += 200;
  });

  return { nodes, edges };
}

export const EntityGraphCanvas = ({ dataset, mapping, onNodeClick, onLayoutChange }: Props) => {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(
    () => buildGraph(dataset, mapping, mapping.layout_state as Record<string, { x: number; y: number }> | undefined),
    [dataset, mapping]
  );
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges] = useEdgesState(initialEdges);

  const handleNodesChange = (changes: unknown[]) => {
    onNodesChange(changes as Parameters<typeof onNodesChange>[0]);

    // Emit layout positions
    const layout: Record<string, { x: number; y: number }> = {};
    const typedChanges = changes as Array<{ id?: string; position?: { x: number; y: number }; type?: string }>;
    const positionChanges: Record<string, { x: number; y: number }> = {};
    typedChanges.forEach((ch) => {
      if (ch.id && ch.position && ch.type === "position") {
        positionChanges[ch.id] = ch.position;
      }
    });

    // Merge with existing positions
    nodes.forEach((n) => {
      const pos = positionChanges[n.id] || n.position;
      layout[n.id] = { x: pos.x, y: pos.y };
    });

    onLayoutChange?.(layout);
  };

  return (
    <ReactFlowProvider>
      <div style={{ height: 500, width: "100%" }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          onNodeClick={(_event, node) => onNodeClick?.(node)}
          onNodesChange={handleNodesChange}
        >
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
};
