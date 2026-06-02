import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { EntityGraphTab } from "@/components/entity-graph/entity-graph-tab";
import type { Dataset, DatasetVersion } from "@/lib/api/types";

// Mock the API module
const mockFetchMapping = vi.fn();
const mockUpdateMapping = vi.fn();
vi.mock("@/lib/api/semantic", () => ({
  fetchMapping: (...args: unknown[]) => mockFetchMapping(...args),
  updateMapping: (...args: unknown[]) => mockUpdateMapping(...args),
}));

// Mock data-source API (used by SourceRegistrationDrawer)
vi.mock("@/lib/api/data-source", () => ({
  fetchDatasets: vi.fn().mockResolvedValue([]),
}));

// Mock toast
vi.mock("@/components/shared", async () => {
  const actual = await vi.importActual("@/components/shared");
  return {
    ...actual,
    useToast: () => ({
      success: vi.fn(),
      info: vi.fn(),
      danger: vi.fn(),
    }),
  };
});

// Mock EntityMappingWizard
vi.mock("@/components/entity-mapping/entity-mapping-wizard", () => ({
  EntityMappingWizard: ({
    onComplete,
    onCancel,
  }: {
    datasetId: string;
    datasetVersionId: string;
    existingMapping: unknown;
    onComplete: () => void;
    onCancel: () => void;
  }) => (
    <div data-testid="entity-mapping-wizard">
      <button data-testid="wizard-complete" onClick={onComplete}>
        Complete
      </button>
      <button data-testid="wizard-cancel" onClick={onCancel}>
        Cancel
      </button>
    </div>
  ),
}));

// Mock ReactFlow to render a simple testable canvas
vi.mock("@xyflow/react", () => ({
  ReactFlow: ({
    nodes,
    edges,
  }: {
    nodes: Array<{ id: string; data: { label: string }; type: string }>;
    edges: Array<{ id: string }>;
  }) => (
    <div data-testid="entity-graph-canvas">
      {nodes.map((node) => (
        <div key={node.id} data-testid={`node-${node.id}`} data-nodetype={node.type}>
          {node.data.label}
        </div>
      ))}
      {edges.map((edge) => (
        <div key={edge.id} data-testid={`edge-${edge.id}`} />
      ))}
    </div>
  ),
  ReactFlowProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
  Background: () => <div data-testid="reactflow-background" />,
  Controls: () => <div data-testid="reactflow-controls" />,
  useNodesState: (initial: Array<{ id: string; data: { label: string } }>) => [initial, vi.fn(), vi.fn()],
  useEdgesState: (initial: Array<{ id: string }>) => [initial, vi.fn(), vi.fn()],
}));

// Mock SourceRegistrationDrawer
vi.mock("@/components/entity-graph/source-registration-drawer", () => ({
  SourceRegistrationDrawer: ({
    sourceNodes,
    onAdd,
    onRemove,
    onClose,
  }: {
    sourceNodes: Array<{ source_id: string; name: string; source_type: string }>;
    onAdd: (node: { source_id: string; name: string; source_type: string; reference_id: string; fields: string[] }) => void;
    onRemove: (sourceId: string) => void;
    onClose: () => void;
  }) => (
    <div data-testid="source-registration-drawer">
      <span data-testid="source-count">{sourceNodes.length}</span>
      <button data-testid="drawer-close" onClick={onClose}>Close</button>
      <button
        data-testid="drawer-add-mock"
        onClick={() =>
          onAdd({
            source_id: "new-src-1",
            source_type: "dataset_table",
            name: "Test Source",
            reference_id: "00000000-0000-0000-0000-000000000001",
            fields: [],
          })
        }
      >
        Add Mock Source
      </button>
      {sourceNodes.map((sn) => (
        <button
          key={sn.source_id}
          data-testid={`drawer-remove-${sn.source_id}`}
          onClick={() => onRemove(sn.source_id)}
        >
          Remove {sn.name}
        </button>
      ))}
    </div>
  ),
}));

// ─── Fixtures ───

const baseVersion: DatasetVersion = {
  id: "version-1",
  dataset_id: "ds-1",
  run_id: "run-1",
  version_number: 1,
  status: "active",
  row_count: 100,
  column_count: 5,
  storage_path: "/test",
  cleaning_issues: [],
  failure_reason: undefined,
  created_at: "2026-01-01T00:00:00Z",
};

const baseDataset: Dataset = {
  id: "ds-1",
  project_id: "proj-1",
  connection_id: "conn-1",
  name: "Test Dataset",
  source_object_name: "test_table",
  status: "active",
  active_version_id: "version-1",
  sync_mode: "batch",
  batch_strategy: "full_snapshot",
  real_time_strategy: null,
  cursor_column: null,
  last_cursor_value: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

// ─── Tests ───

describe("EntityGraphTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ─── Loading State ───

  it("shows loading spinner while fetching mapping", () => {
    mockFetchMapping.mockReturnValue(new Promise(() => {})); // never resolves
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    expect(screen.getByText("Loading entity graph...")).toBeInTheDocument();
  });

  // ─── Empty State (No Mapping) ───

  it("shows empty state with prompt when no mapping exists", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    expect(
      screen.getByText(
        /Map dataset columns to a reusable Object Type/i
      )
    ).toBeInTheDocument();

    const createBtn = screen.getByText("Configure Entity Mapping");
    expect(createBtn).toBeInTheDocument();
  });

  it("opens entity mapping wizard when 'Configure Entity Mapping' is clicked from empty state", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Configure Entity Mapping"));

    expect(screen.getByTestId("entity-mapping-wizard")).toBeInTheDocument();
  });

  // ─── Graph Canvas with Entity Node ───

  const baseMapping = {
    id: "map-1",
    dataset_id: "ds-1",
    dataset_version_id: "version-1",
    version_number: 1,
    object_type_id: "ot-1",
    object_type_key: "employee",
    properties: [
      {
        source_column: "id",
        property_name: "ID",
        semantic_type: "integer",
        included: true,
        is_primary_key: true,
      },
    ],
    links: [],
    source_nodes: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
  };

  it("shows graph canvas with Entity node when mapping exists", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByTestId("entity-graph-canvas")).toBeInTheDocument();
    });

    // Entity node shows the object type key as label
    expect(screen.getByTestId("node-entity")).toBeInTheDocument();
    expect(screen.getByTestId("node-entity")).toHaveTextContent("employee");
  });

  it("shows dataset lineage nodes on graph", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByTestId("entity-graph-canvas")).toBeInTheDocument();
    });

    // Dataset node shows dataset name
    expect(screen.getByTestId("node-dataset")).toBeInTheDocument();
    expect(screen.getByTestId("node-dataset")).toHaveTextContent("Test Dataset");
  });

  it("shows existing link references as edges", async () => {
    const mappingWithLinks = {
      ...baseMapping,
      links: [
        {
          link_id: "dept_link",
          display_name: "Department",
          source_property_key: "dept_id",
          target_object_type_id: "ot-dept",
          target_property_key: "id",
          cardinality: "many_to_one",
        },
      ],
    };
    mockFetchMapping.mockResolvedValue(mappingWithLinks);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByTestId("entity-graph-canvas")).toBeInTheDocument();
    });

    // Edge exists from entity to target
    expect(screen.getByTestId("edge-entity-ot-dept")).toBeInTheDocument();

    // Target node shows the link display name
    expect(screen.getByTestId("node-target-ot-dept")).toBeInTheDocument();
    expect(screen.getByTestId("node-target-ot-dept")).toHaveTextContent(
      "Department"
    );
  });

  // ─── Slice 2: Source Registration Drawer ───

  it("shows 'Add Source' button when mapping exists", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByTestId("entity-graph-canvas")).toBeInTheDocument();
    });

    expect(screen.getByText("+ Add Source")).toBeInTheDocument();
  });

  it("opens source registration drawer when 'Add Source' is clicked", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("+ Add Source")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Source"));

    expect(screen.getByTestId("source-registration-drawer")).toBeInTheDocument();
  });

  it("adds source node to graph when registered via drawer", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("+ Add Source")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Source"));
    fireEvent.click(screen.getByTestId("drawer-add-mock"));

    // Source node should appear on the graph
    await waitFor(() => {
      expect(screen.getByTestId("node-source-node-new-src-1")).toBeInTheDocument();
    });
    expect(screen.getByTestId("node-source-node-new-src-1")).toHaveTextContent(
      "Test Source"
    );
  });

  it("removes source node when removed via drawer", async () => {
    const mappingWithSources = {
      ...baseMapping,
      source_nodes: [
        {
          source_id: "src-1",
          source_type: "dataset_table",
          name: "My Table",
          reference_id: "ref-1",
          fields: [],
        },
      ],
    };
    mockFetchMapping.mockResolvedValue(mappingWithSources);
    render(<EntityGraphTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("+ Add Source")).toBeInTheDocument();
    });

    // Source node should exist initially
    expect(screen.getByTestId("node-source-node-src-1")).toBeInTheDocument();

    fireEvent.click(screen.getByText("+ Add Source"));
    expect(screen.getByTestId("source-registration-drawer")).toBeInTheDocument();

    // Remove the source
    fireEvent.click(screen.getByTestId("drawer-remove-src-1"));

    // Source node should be gone from graph
    await waitFor(() => {
      expect(
        screen.queryByTestId("node-source-node-src-1")
      ).not.toBeInTheDocument();
    });
  });
});
