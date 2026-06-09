import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SourceRegistrationDrawer } from "@/components/entity-graph/source-registration-drawer";
import type { Dataset, Connection, SourceNode } from "@/lib/api/types";

// ── Mock API modules ──

const mockFetchDatasets = vi.fn();
const mockFetchConnections = vi.fn();

vi.mock("@/lib/api/data-source", () => ({
  fetchDatasets: (...args: unknown[]) => mockFetchDatasets(...args),
  fetchConnections: (...args: unknown[]) => mockFetchConnections(...args),
}));

const mockFetchDatasetVersionSchema = vi.fn();
vi.mock("@/lib/api/semantic", () => ({
  fetchDatasetVersionSchema: (...args: unknown[]) => mockFetchDatasetVersionSchema(...args),
}));

// ── Fixtures ──

const baseDataset = (overrides: Partial<Dataset> = {}): Dataset => ({
  id: "ds-1",
  project_id: "proj-1",
  connection_id: "conn-1",
  name: "employees",
  source_object_name: "employees_raw",
  status: "active",
  active_version_id: "version-1",
  sync_mode: "batch",
  batch_strategy: "full_snapshot",
  real_time_strategy: null,
  cursor_column: null,
  last_cursor_value: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

const baseConnection = (overrides: Partial<Connection> = {}): Connection => ({
  id: "conn-static-1",
  project_id: "proj-1",
  name: "budget.xlsx",
  source_type: "static_file",
  status: "connected",
  config_json: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
  ...overrides,
});

// Shared API data
const datasets = [
  baseDataset({ id: "ds-1", name: "employees", source_object_name: "employees_raw" }),
  baseDataset({ id: "ds-2", name: "departments", source_object_name: "departments" }),
];
const connections = [
  baseConnection({ id: "conn-1", name: "budget.xlsx", source_type: "static_file" }),
  baseConnection({ id: "conn-2", name: "headcount.xlsx", source_type: "static_file" }),
];

// ── Props helper ──

const defaultProps = {
  projectId: "proj-1",
  datasetId: "ds-1",
  sourceNodes: [],
  onAdd: vi.fn().mockResolvedValue(undefined),
  onRemove: vi.fn(),
  onClose: vi.fn(),
};

// ── Tests ──

describe("SourceRegistrationDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchDatasets.mockResolvedValue(datasets);
    mockFetchConnections.mockResolvedValue(connections);
  });

  it("renders checkbox list of available dataset and static-file sources", async () => {
    render(<SourceRegistrationDrawer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // ds-1 employees_raw excluded because it matches datasetId (circular)
    // 3 remaining: departments, budget.xlsx, headcount.xlsx
    expect(screen.queryByText("employees_raw")).not.toBeInTheDocument();
    expect(screen.getByText("departments")).toBeInTheDocument();
    expect(screen.getByText("budget.xlsx")).toBeInTheDocument();
    expect(screen.getByText("headcount.xlsx")).toBeInTheDocument();

    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(3);
  });

  it("adds successfully fetched sources and skips failed ones on partial failure", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    // Make schema fetch fail for dataset sources
    mockFetchDatasetVersionSchema.mockRejectedValue(new Error("Schema unavailable"));

    render(
      <SourceRegistrationDrawer
        {...defaultProps}
        onAdd={onAdd}
        onClose={onClose}
      />
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // Select departments (dataset_table, will fail) and budget.xlsx (static_file, will succeed)
    fireEvent.click(screen.getByText("departments"));
    fireEvent.click(screen.getByText("budget.xlsx"));

    expect(screen.getByText("2 selected")).toBeInTheDocument();

    // Click Add Sources
    fireEvent.click(screen.getByRole("button", { name: /Add Sources/ }));

    // Wait for async add — onAdd should be called with only the successful source
    await waitFor(() => {
      expect(onAdd).toHaveBeenCalledTimes(1);
    });

    const nodes = onAdd.mock.calls[0][0] as Array<{ source_id: string; name: string }>;
    // Only the static file should succeed
    expect(nodes).toHaveLength(1);
    expect(nodes[0].name).toBe("budget.xlsx");

    // Drawer closes even on partial failure
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onAdd with array of SourceNodes when Add Sources is clicked", async () => {
    const onAdd = vi.fn().mockResolvedValue(undefined);
    const onClose = vi.fn();

    mockFetchDatasetVersionSchema.mockResolvedValue([
      { column_name: "id", data_type: "integer", nullable: false },
      { column_name: "name", data_type: "string", nullable: false },
      { column_name: "budget", data_type: "number", nullable: true },
    ]);

    render(
      <SourceRegistrationDrawer
        {...defaultProps}
        onAdd={onAdd}
        onClose={onClose}
      />
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // Select departments (ds-2, dataset_table) and budget.xlsx (conn-1, static_file)
    fireEvent.click(screen.getByText("departments"));
    fireEvent.click(screen.getByText("budget.xlsx"));

    // Counter shows 2 selected
    expect(screen.getByText("2 selected")).toBeInTheDocument();

    // Click the "Add Sources" button
    fireEvent.click(screen.getByRole("button", { name: /Add Sources/ }));

    // Wait for the async add to complete
    await waitFor(() => {
      expect(onAdd).toHaveBeenCalledTimes(1);
    });

    const nodes = onAdd.mock.calls[0][0] as Array<{ source_id: string; source_type: string; name: string; reference_id: string; fields: string[] }>;

    expect(nodes).toHaveLength(2);

    // First node: departments (dataset_table with schema fetched)
    expect(nodes[0]).toMatchObject({
      source_id: "src-ds-2",
      source_type: "dataset_table",
      name: "departments",
      reference_id: "ds-2",
    });
    expect(nodes[0].fields).toEqual(["id", "name", "budget"]);

    // Second node: budget.xlsx (static_file, no schema fetch)
    expect(nodes[1]).toMatchObject({
      source_id: "src-conn-1",
      source_type: "static_file",
      name: "budget.xlsx",
      reference_id: "conn-1",
    });
    expect(nodes[1].fields).toEqual([]);

    // Drawer closes
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("supports Select All and Deselect All", async () => {
    render(<SourceRegistrationDrawer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // Initially no checkboxes selected
    expect(screen.queryByText(/selected/)).not.toBeInTheDocument();

    // Click Select All
    fireEvent.click(screen.getByText("Select All"));

    // All 3 checkboxes should be checked
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(3);
    checkboxes.forEach((cb) => {
      expect(cb).toBeChecked();
    });

    // "N selected" counter should appear
    expect(screen.getByText("3 selected")).toBeInTheDocument();

    // Click Deselect All
    fireEvent.click(screen.getByText("Deselect All"));

    // All checkboxes unchecked
    checkboxes.forEach((cb) => {
      expect(cb).not.toBeChecked();
    });

    // Counter gone
    expect(screen.queryByText(/selected/)).not.toBeInTheDocument();
  });

  it("filters the checkbox list when search query is typed", async () => {
    render(<SourceRegistrationDrawer {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // Initially 3 sources shown
    expect(screen.getByText("departments")).toBeInTheDocument();
    expect(screen.getByText("budget.xlsx")).toBeInTheDocument();
    expect(screen.getByText("headcount.xlsx")).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(3);

    // Type a search query
    const searchInput = screen.getByPlaceholderText("Search sources...");
    fireEvent.change(searchInput, { target: { value: "budget" } });

    // Only budget.xlsx matches
    expect(screen.queryByText("departments")).not.toBeInTheDocument();
    expect(screen.getByText("budget.xlsx")).toBeInTheDocument();
    expect(screen.queryByText("headcount.xlsx")).not.toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(1);

    // Clear the search
    fireEvent.change(searchInput, { target: { value: "" } });

    // All 3 back
    expect(screen.getByText("departments")).toBeInTheDocument();
    expect(screen.getByText("budget.xlsx")).toBeInTheDocument();
    expect(screen.getByText("headcount.xlsx")).toBeInTheDocument();
    expect(screen.getAllByRole("checkbox")).toHaveLength(3);
  });

  it("hides already-registered sources from the checkbox list", async () => {
    const existingNodes: SourceNode[] = [
      {
        source_id: "src-ds-2",
        source_type: "dataset_table",
        name: "departments",
        reference_id: "ds-2",
        fields: ["id", "name"],
      },
    ];

    render(
      <SourceRegistrationDrawer
        {...defaultProps}
        sourceNodes={existingNodes}
      />
    );

    await waitFor(() => {
      expect(screen.queryByText(/Loading sources/)).not.toBeInTheDocument();
    });

    // departments IS in the DOM (shown in the existing source nodes section at top)
    expect(screen.getByText("departments")).toBeInTheDocument();

    // Static files still visible in the ADD section
    expect(screen.getByText("budget.xlsx")).toBeInTheDocument();
    expect(screen.getByText("headcount.xlsx")).toBeInTheDocument();

    // 2 checkboxes: static files only (ds-1 excluded as current, ds-2 already registered)
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes).toHaveLength(2);
  });
});
