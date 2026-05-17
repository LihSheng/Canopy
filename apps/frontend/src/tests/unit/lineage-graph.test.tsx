import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { LineageGraph } from "@/components/ingestion-v2/lineage-graph";

const mockFetchLineage = vi.fn();

vi.mock("@/lib/api/ingestion", () => ({
  fetchLineage: (...args: unknown[]) => mockFetchLineage(...args),
}));

const SAMPLE_NODES = [
  { id: "file:u1", node_type: "file", label: "data.xlsx", metadata: {} },
  { id: "sheet:u1", node_type: "sheet", label: "Sheet1", metadata: {} },
  { id: "raw:u1:name", node_type: "raw_column", label: "name", metadata: {} },
  { id: "raw:u1:amount", node_type: "raw_column", label: "amount", metadata: {} },
  { id: "cleaned:u1:name", node_type: "cleaned_field", label: "name", metadata: {} },
  { id: "cleaned:u1:amount", node_type: "cleaned_field", label: "amount", metadata: {} },
  { id: "onto:u1:employee_name", node_type: "ontology_field", label: "employee_name", metadata: {} },
  { id: "onto:u1:salary", node_type: "ontology_field", label: "salary", metadata: {} },
];

const SAMPLE_EDGES = [
  { id: "e1", from_node_id: "sheet:u1", to_node_id: "file:u1", edge_type: "derived_from", metadata: {} },
  { id: "e2", from_node_id: "raw:u1:name", to_node_id: "sheet:u1", edge_type: "derived_from", metadata: {} },
  { id: "e3", from_node_id: "raw:u1:amount", to_node_id: "sheet:u1", edge_type: "derived_from", metadata: {} },
  { id: "e4", from_node_id: "raw:u1:name", to_node_id: "cleaned:u1:name", edge_type: "derived_from", metadata: {} },
  { id: "e5", from_node_id: "raw:u1:amount", to_node_id: "cleaned:u1:amount", edge_type: "derived_from", metadata: {} },
  { id: "e6", from_node_id: "cleaned:u1:name", to_node_id: "onto:u1:employee_name", edge_type: "normalized_to", metadata: {} },
  { id: "e7", from_node_id: "cleaned:u1:amount", to_node_id: "onto:u1:salary", edge_type: "normalized_to", metadata: {} },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("LineageGraph", () => {
  it("renders loading state initially", () => {
    mockFetchLineage.mockReturnValue(new Promise(() => {}));
    render(<LineageGraph uploadId="u1" />);
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("renders all node layers from the graph", async () => {
    mockFetchLineage.mockResolvedValue({
      upload_id: "u1",
      nodes: SAMPLE_NODES,
      edges: SAMPLE_EDGES,
    });

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("data.xlsx")).toBeInTheDocument();
      expect(screen.getByText("Sheet1")).toBeInTheDocument();
      expect(screen.getByText("employee_name")).toBeInTheDocument();
      expect(screen.getByText("salary")).toBeInTheDocument();
    });

    const nameElements = screen.getAllByText("name");
    expect(nameElements.length).toBe(2);
    expect(screen.getAllByText("amount").length).toBe(2);
  });

  it("shows layer labels for each type", async () => {
    mockFetchLineage.mockResolvedValue({
      upload_id: "u1",
      nodes: SAMPLE_NODES,
      edges: SAMPLE_EDGES,
    });

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("File")).toBeInTheDocument();
      expect(screen.getByText("Sheet")).toBeInTheDocument();
      expect(screen.getByText("Raw Column")).toBeInTheDocument();
      expect(screen.getByText("Cleaned Field")).toBeInTheDocument();
      expect(screen.getByText("Ontology Field")).toBeInTheDocument();
    });
  });

  it("renders empty state when no nodes", async () => {
    mockFetchLineage.mockResolvedValue({
      upload_id: "u1",
      nodes: [],
      edges: [],
    });

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("No lineage data available for this upload.")).toBeInTheDocument();
    });
  });

  it("shows error state on fetch failure", async () => {
    mockFetchLineage.mockRejectedValue(new Error("Network error"));

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("highlights connected nodes on hover", async () => {
    mockFetchLineage.mockResolvedValue({
      upload_id: "u1",
      nodes: SAMPLE_NODES,
      edges: SAMPLE_EDGES,
    });

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("data.xlsx")).toBeInTheDocument();
    });

    const sheetNode = screen.getByText("Sheet1");
    fireEvent.mouseEnter(sheetNode);

    const fileNode = screen.getByText("data.xlsx");
    expect(fileNode.className).not.toContain("opacity-30");
  });

  it("shows metadata panel on node click", async () => {
    const nodesWithMeta = [
      { id: "cleaned:u1:name", node_type: "cleaned_field", label: "name", metadata: { cleaning_steps: [{ step_type: "trim", order: 0 }] } },
    ];
    mockFetchLineage.mockResolvedValue({
      upload_id: "u1",
      nodes: nodesWithMeta,
      edges: [],
    });

    render(<LineageGraph uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("name")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("name"));

    await waitFor(() => {
      expect(screen.getByText("cleaning_steps:")).toBeInTheDocument();
    });
  });
});
