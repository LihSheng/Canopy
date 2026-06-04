import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EntityLineageCanvas } from "@/components/entity-graph/entity-lineage-canvas";
import type { EntityLineageGraph } from "@/lib/api/types";

// ReactFlow uses canvas-based rendering; we verify the container renders and
// the component mounts without errors. Deeper rendering checks are done
// through the entity detail page integration tests.

const baseLineage: EntityLineageGraph = {
  entity_id: "ent-1",
  entity_label: "Employee",
  nodes: [
    {
      id: "entity",
      kind: "entity",
      label: "Employee",
      properties: ["Full Name", "Salary"],
      collapsed: false,
      collapsed_count: 0,
      subtype: "",
    },
    {
      id: "dataset",
      kind: "dataset",
      label: "HR Master",
      properties: [],
      collapsed: false,
      collapsed_count: 0,
      subtype: "",
    },
    {
      id: "dataset-version",
      kind: "derived",
      label: "v3",
      properties: [],
      collapsed: false,
      collapsed_count: 0,
      subtype: "dataset_version",
    },
    {
      id: "source-node-src-1",
      kind: "source",
      label: "employees.csv",
      properties: [],
      collapsed: false,
      collapsed_count: 0,
      subtype: "",
    },
  ],
  edges: [
    {
      id: "dataset-to-dv",
      kind: "lineage",
      source_id: "dataset",
      target_id: "dataset-version",
      label: "",
      source_handle: "",
      target_handle: "",
    },
    {
      id: "dv-to-entity",
      kind: "lineage",
      source_id: "dataset-version",
      target_id: "entity",
      label: "",
      source_handle: "",
      target_handle: "",
    },
    {
      id: "src-to-dv",
      kind: "lineage",
      source_id: "source-node-src-1",
      target_id: "dataset-version",
      label: "",
      source_handle: "",
      target_handle: "",
    },
    {
      id: "bind-name",
      kind: "binding",
      source_id: "source-node-src-1",
      target_id: "entity",
      label: "name",
      source_handle: "name",
      target_handle: "full_name",
    },
  ],
  layout_state: {},
};

describe("EntityLineageCanvas", () => {
  it("renders without error with valid lineage data", () => {
    const { container } = render(<EntityLineageCanvas lineage={baseLineage} />);
    // ReactFlow renders into a container div
    expect(container.querySelector(".react-flow")).toBeInTheDocument();
  });

  it("renders entity label with properties", () => {
    const { container } = render(<EntityLineageCanvas lineage={baseLineage} />);
    // The entity node's label includes properties in brackets
    expect(container.textContent).toContain("Employee");
    expect(container.textContent).toContain("Full Name");
    expect(container.textContent).toContain("Salary");
  });

  it("renders dataset and version context nodes", () => {
    const { container } = render(<EntityLineageCanvas lineage={baseLineage} />);
    expect(container.textContent).toContain("HR Master");
    expect(container.textContent).toContain("v3");
  });

  it("renders source nodes", () => {
    const { container } = render(<EntityLineageCanvas lineage={baseLineage} />);
    expect(container.textContent).toContain("employees.csv");
  });

  it("renders with minimal lineage (entity-only)", () => {
    const minimal: EntityLineageGraph = {
      entity_id: "ent-2",
      entity_label: "Minimal",
      nodes: [
        {
          id: "entity",
          kind: "entity",
          label: "Minimal",
          properties: [],
          collapsed: false,
          collapsed_count: 0,
          subtype: "",
        },
      ],
      edges: [],
      layout_state: {},
    };
    const { container } = render(<EntityLineageCanvas lineage={minimal} />);
    expect(container.querySelector(".react-flow")).toBeInTheDocument();
    expect(container.textContent).toContain("Minimal");
  });
});

describe("EntityLineageCanvas — derived chain collapse/expand", () => {
  const derivedChainLineage: EntityLineageGraph = {
    entity_id: "ent-3",
    entity_label: "Product",
    nodes: [
      {
        id: "entity",
        kind: "entity",
        label: "Product",
        properties: ["SKU", "Price"],
        collapsed: false,
        collapsed_count: 0,
        subtype: "",
      },
      {
        id: "derived-clean",
        kind: "derived",
        label: "Cleaned Products",
        properties: [],
        collapsed: false,
        collapsed_count: 0,
        subtype: "",
      },
      {
        id: "derived-enrich",
        kind: "derived",
        label: "Enriched Products",
        properties: [],
        collapsed: false,
        collapsed_count: 0,
        subtype: "",
      },
      {
        id: "source-node-raw",
        kind: "source",
        label: "raw_products.csv",
        properties: [],
        collapsed: false,
        collapsed_count: 0,
        subtype: "",
      },
    ],
    edges: [
      {
        id: "raw-to-clean",
        kind: "lineage",
        source_id: "source-node-raw",
        target_id: "derived-clean",
        label: "",
        source_handle: "",
        target_handle: "",
      },
      {
        id: "clean-to-enrich",
        kind: "lineage",
        source_id: "derived-clean",
        target_id: "derived-enrich",
        label: "",
        source_handle: "",
        target_handle: "",
      },
      {
        id: "enrich-to-entity",
        kind: "lineage",
        source_id: "derived-enrich",
        target_id: "entity",
        label: "",
        source_handle: "",
        target_handle: "",
      },
    ],
    layout_state: {},
  };

  it("loads fully expanded by default (all derived nodes visible)", () => {
    const { container } = render(
      <EntityLineageCanvas lineage={derivedChainLineage} />
    );
    // All derived nodes should be visible on load
    expect(container.textContent).toContain("Cleaned Products");
    expect(container.textContent).toContain("Enriched Products");
    // No collapse summary text
    expect(container.textContent).not.toContain("hidden");
  });

  it("derived node labels are shown in default view", () => {
    const { container } = render(
      <EntityLineageCanvas lineage={derivedChainLineage} />
    );
    // Both derived nodes should be visible
    expect(container.textContent).toContain("Cleaned Products");
    expect(container.textContent).toContain("Enriched Products");
  });
});
