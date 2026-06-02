import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { EntityTab } from "@/components/entity-mapping/entity-tab";
import type { Dataset, DatasetVersion } from "@/lib/api/types";

// Mock the API module
const mockFetchMapping = vi.fn();
vi.mock("@/lib/api/semantic", () => ({
  fetchMapping: (...args: unknown[]) => mockFetchMapping(...args),
}));

// Mock EntityMappingWizard (tested separately)
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
    {
      source_column: "name",
      property_name: "Name",
      semantic_type: "string",
      included: true,
      is_primary_key: false,
    },
  ],
  links: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
};

// ─── Tests ───

describe("EntityTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ─── Loading State ───

  it("shows loading spinner while fetching mapping", () => {
    mockFetchMapping.mockReturnValue(new Promise(() => {})); // never resolves
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    expect(screen.getByText("Loading entity mapping...")).toBeInTheDocument();
  });

  // ─── Error State ───

  it("shows error state when fetch fails", async () => {
    mockFetchMapping.mockRejectedValue(new Error("Network failure"));
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("Network failure")).toBeInTheDocument();
    });
  });

  // ─── No Active Version ───

  it("shows empty state when no active version exists", async () => {
    mockFetchMapping.mockResolvedValue(null);
    const datasetWithoutActive = {
      ...baseDataset,
      active_version_id: "nonexistent",
    };
    render(
      <EntityTab
        dataset={datasetWithoutActive}
        versions={[baseVersion]}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No active dataset version")).toBeInTheDocument();
    });
    // fetchMapping should NOT have been called (no active version to fetch for)
    expect(mockFetchMapping).not.toHaveBeenCalled();
  });

  // ─── Empty (No Mapping) State ───

  it("shows empty mapping state with 'Configure Entity Mapping' button when no mapping exists", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    const configureBtn = screen.getByText("Configure Entity Mapping");
    expect(configureBtn).toBeInTheDocument();
  });

  // ─── Mapping View State ───

  it("shows mapping view with properties table when mapping exists", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("Entity Mapping")).toBeInTheDocument();
    });

    // "v1" spans multiple text nodes in the JSX template literal
    expect(screen.getByText(/v1/)).toBeInTheDocument();
    expect(screen.getByText(/employee/)).toBeInTheDocument();

    // Property table columns
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();

    // PK badge
    expect(screen.getByText("PK")).toBeInTheDocument();

    // Edit button
    expect(screen.getByText("Edit Mapping")).toBeInTheDocument();
  });

  it("shows links table when mapping has links", async () => {
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
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(
        screen.getByText("Entity Relationship Links (1)")
      ).toBeInTheDocument();
    });

    expect(screen.getByText("dept_link")).toBeInTheDocument();
    expect(screen.getByText("Department")).toBeInTheDocument();
    expect(screen.getByText("many_to_one")).toBeInTheDocument();
  });

  // ─── Wizard Open State ───

  it("renders wizard when 'Configure Entity Mapping' is clicked", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Configure Entity Mapping"));

    expect(screen.getByTestId("entity-mapping-wizard")).toBeInTheDocument();
  });

  it("renders wizard with 'Edit' title when editing existing mapping", async () => {
    mockFetchMapping.mockResolvedValue(baseMapping);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("Edit Mapping")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Edit Mapping"));

    await waitFor(() => {
      expect(screen.getByText("Edit Entity Mapping")).toBeInTheDocument();
    });
    expect(screen.getByTestId("entity-mapping-wizard")).toBeInTheDocument();
  });

  // ─── Wizard Cancel ───

  it("returns to empty state when wizard is cancelled", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Configure Entity Mapping"));
    expect(screen.getByTestId("entity-mapping-wizard")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("wizard-cancel"));

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });
  });

  // ─── Wizard Complete ───

  it("reloads mapping when wizard completes", async () => {
    mockFetchMapping.mockResolvedValue(null);
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("No entity mapping yet")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Configure Entity Mapping"));
    expect(screen.getByTestId("entity-mapping-wizard")).toBeInTheDocument();

    // Set up mock to return mapping after complete triggers reload
    mockFetchMapping.mockResolvedValue(baseMapping);
    fireEvent.click(screen.getByTestId("wizard-complete"));

    await waitFor(() => {
      expect(screen.getByText("Entity Mapping")).toBeInTheDocument();
    });
    expect(screen.getByText("Edit Mapping")).toBeInTheDocument();
  });

  // ─── Retry on Error ───

  it("retries fetch when error state retry is clicked", async () => {
    mockFetchMapping.mockRejectedValueOnce(new Error("First fail"));
    render(<EntityTab dataset={baseDataset} versions={[baseVersion]} />);

    await waitFor(() => {
      expect(screen.getByText("First fail")).toBeInTheDocument();
    });

    mockFetchMapping.mockResolvedValue(baseMapping);
    fireEvent.click(screen.getByText("Try again"));

    await waitFor(() => {
      expect(screen.getByText("Entity Mapping")).toBeInTheDocument();
    });
  });
});
