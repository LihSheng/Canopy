import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mock_push = vi.fn();
const mock_replace = vi.fn();
let mock_search_params = new URLSearchParams();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mock_push, replace: mock_replace }),
  useSearchParams: () => mock_search_params,
}));

vi.mock("@/lib/api/data-source", () => ({
  fetchDataset: vi.fn(),
  fetchDatasetDeleteSummary: vi.fn(),
  fetchDatasetPreview: vi.fn(),
  fetchDatasetVersions: vi.fn(),
  fetchDatasetHealth: vi.fn(),
  fetchDatasetLineage: vi.fn(),
  fetchRuns: vi.fn(),
  deleteDataset: vi.fn(),
  deleteDatasetVersion: vi.fn(),
  updateDataset: vi.fn(),
  fetchConnection: vi.fn(),
  previewStaticFile: vi.fn(),
  reimportDatasetVersion: vi.fn(),
  refreshDatasetVersion: vi.fn(),
  fetchRetentionPolicy: vi.fn(),
  saveRetentionPolicy: vi.fn(),
}));

vi.mock("@/lib/api/semantic", () => ({
  fetchDatasetVersionSchema: vi.fn(),
}));

const mock_toast = {
  success: vi.fn(),
  info: vi.fn(),
  warning: vi.fn(),
  danger: vi.fn(),
  showToast: vi.fn(),
};

vi.mock("@/components/shared/toast", () => ({
  useToast: () => mock_toast,
}));

import DatasetWorkspaceContent from "@/app/dashboard/connections/datasets/[id]/dataset-workspace-content";
import * as api from "@/lib/api/data-source";
import * as semanticApi from "@/lib/api/semantic";

describe("Dataset workspace delete actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mock_search_params = new URLSearchParams();
  });

  function mockWorkspaceData() {
    vi.mocked(api.fetchDataset).mockResolvedValue({
      id: "dataset-1",
      project_id: "proj-1",
      connection_id: "conn-1",
      name: "Leave Application Report",
      source_object_name: "Payroll",
      status: "active",
      active_version_id: "version-1",
      created_at: "2026-05-18T00:00:00Z",
      updated_at: "2026-05-18T00:00:00Z",
    });
    vi.mocked(api.fetchDatasetDeleteSummary).mockResolvedValue({
      dataset_id: "dataset-1",
      version_count: 2,
      active_run_count: 0,
      can_delete: true,
      blocking_reason: null,
    });
    vi.mocked(api.fetchDatasetVersions).mockResolvedValue([
      {
        id: "version-1",
        dataset_id: "dataset-1",
        run_id: "run-1",
        version_number: 1,
        status: "ready",
        row_count: 9,
        column_count: 12,
        storage_path: "/data/v1",
        cleaning_issues: [],
        created_at: "2026-05-18T00:00:00Z",
      },
      {
        id: "version-2",
        dataset_id: "dataset-1",
        run_id: "run-2",
        version_number: 2,
        status: "ready",
        row_count: 10,
        column_count: 12,
        storage_path: "/data/v2",
        cleaning_issues: [],
        created_at: "2026-05-18T00:00:00Z",
      },
    ]);
    vi.mocked(api.fetchDatasetHealth).mockResolvedValue({
      dataset_id: "dataset-1",
      row_count: 9,
      column_count: 12,
      missing_required_mappings: false,
      warning_count: 0,
      last_run_status: null,
      last_published_version: 1,
      freshness_at: null,
      schema_drift: null,
    });
    vi.mocked(api.fetchDatasetLineage).mockResolvedValue({
      nodes: [],
      edges: [],
    });
    vi.mocked(api.fetchRuns).mockResolvedValue([]);
    vi.mocked(api.fetchDatasetPreview).mockResolvedValue({
      columns: ["name", "amount"],
      rows: [["Alice", 100]],
      total_row_count: 1,
      page: 1,
      page_size: 100,
    });
    vi.mocked(api.fetchConnection).mockResolvedValue({
      id: "conn-1",
      project_id: "proj-1",
      source_type: "postgres",
      name: "My Postgres",
      status: "connected",
      config_json: { supports_cdc: true },
      created_at: "2026-05-18T00:00:00Z",
      updated_at: "2026-05-18T00:00:00Z",
    });
    vi.mocked(semanticApi.fetchDatasetVersionSchema).mockResolvedValue([
      { column_name: "id", primitive_type: "integer" },
      { column_name: "created_at", primitive_type: "datetime" },
      { column_name: "name", primitive_type: "string" },
    ]);
  }

  function mockStaticWorkspaceData() {
    mockWorkspaceData();
    vi.mocked(api.fetchConnection).mockResolvedValue({
      id: "conn-1",
      project_id: "proj-1",
      source_type: "static_file",
      name: "My File",
      status: "connected",
      config_json: { source_file_path: "/tmp/source.xlsx" },
      created_at: "2026-05-18T00:00:00Z",
      updated_at: "2026-05-18T00:00:00Z",
    });
  }

  it("shows delete dataset in the header and routes after delete", async () => {
    mockWorkspaceData();
    vi.mocked(api.deleteDataset).mockResolvedValue({ deleted: true, id: "dataset-1" });

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Delete Dataset" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Delete Dataset" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Delete dataset?")).toBeInTheDocument();
    });

    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete Dataset" }));

    await waitFor(() => {
      expect(api.deleteDataset).toHaveBeenCalledWith("dataset-1");
      expect(mock_toast.success).toHaveBeenCalledWith(
        "Dataset deleted",
        "Leave Application Report was removed.",
      );
      expect(mock_push).toHaveBeenCalledWith("/dashboard/connections/datasets");
    });
  });

  it("shows dataset delete lock copy when active runs block delete", async () => {
    mockWorkspaceData();
    vi.mocked(api.fetchDatasetDeleteSummary).mockResolvedValue({
      dataset_id: "dataset-1",
      version_count: 2,
      active_run_count: 1,
      can_delete: false,
      blocking_reason: "Dataset has 1 active run(s)",
    });

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByText("Dataset delete is locked.")).toBeInTheDocument();
    });

    expect(screen.getByText(/Remove active runs before deleting this dataset/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete Dataset" })).toBeDisabled();
  });

  it("shows delete version inside the Versions tab for non-active versions", async () => {
    mockWorkspaceData();
    mock_search_params = new URLSearchParams("tab=Versions");
    vi.mocked(api.deleteDatasetVersion).mockResolvedValue({
      deleted: true,
      id: "version-2",
    });

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete Version" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete Version" }));

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
      expect(screen.getByText("Delete version?")).toBeInTheDocument();
    });

    fireEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Delete Version" }));

    await waitFor(() => {
      expect(api.deleteDatasetVersion).toHaveBeenCalledWith("dataset-1", "version-2");
      expect(mock_toast.success).toHaveBeenCalledWith(
        "Version deleted",
        "v2 was removed from Leave Application Report.",
      );
    });
  });

  it("refreshes the latest version with the same button for database sources", async () => {
    mockWorkspaceData();
    mock_search_params = new URLSearchParams("tab=Versions");
    vi.mocked(api.refreshDatasetVersion).mockResolvedValue({
      id: "version-3",
      dataset_id: "dataset-1",
      run_id: "run-3",
      version_number: 3,
      status: "ready",
      row_count: 11,
      column_count: 12,
      storage_path: "/data/v3",
      cleaning_issues: [],
      created_at: "2026-05-19T00:00:00Z",
    });

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Refresh Latest" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Refresh Latest" }));

    await waitFor(() => {
      expect(api.refreshDatasetVersion).toHaveBeenCalledWith("dataset-1");
      expect(mock_toast.success).toHaveBeenCalledWith(
        "Latest data refreshed",
        "v3 is now active.",
      );
    });
  });

  it("opens file picker with the same button for static file sources", async () => {
    mockStaticWorkspaceData();
    mock_search_params = new URLSearchParams("tab=Versions");
    const clickSpy = vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(() => {});

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Refresh Latest" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Refresh Latest" }));

    expect(clickSpy).toHaveBeenCalledTimes(1);
    expect(api.refreshDatasetVersion).not.toHaveBeenCalled();
    clickSpy.mockRestore();
  });

  describe("inline dataset rename", () => {
    it("shows the dataset name and an edit button", async () => {
      mockWorkspaceData();
      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      const editButton = screen.getByTitle("Click to rename dataset");
      expect(editButton).toBeInTheDocument();
    });

    it("switches to input when edit button is clicked", async () => {
      mockWorkspaceData();
      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTitle("Click to rename dataset"));

      const input = screen.getByDisplayValue("Leave Application Report");
      expect(input).toBeInTheDocument();
    });

    it("calls updateDataset and reloads on Enter", async () => {
      mockWorkspaceData();
      vi.mocked(api.updateDataset).mockResolvedValue({
        id: "dataset-1",
        project_id: "proj-1",
        connection_id: "conn-1",
        name: "Renamed Report",
        source_object_name: "Payroll",
        status: "active",
        active_version_id: "version-1",
        created_at: "2026-05-18T00:00:00Z",
        updated_at: "2026-05-18T00:00:00Z",
      });

      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTitle("Click to rename dataset"));

      const input = screen.getByDisplayValue("Leave Application Report");
      fireEvent.change(input, { target: { value: "Renamed Report" } });
      fireEvent.keyDown(input, { key: "Enter" });

      await waitFor(() => {
        expect(api.updateDataset).toHaveBeenCalledWith("dataset-1", { name: "Renamed Report" });
        expect(mock_toast.success).toHaveBeenCalledWith(
          "Dataset renamed",
          'Renamed to "Renamed Report".',
        );
      });
    });

    it("shows validation error for empty name", async () => {
      mockWorkspaceData();
      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTitle("Click to rename dataset"));

      const input = screen.getByDisplayValue("Leave Application Report");
      fireEvent.change(input, { target: { value: "   " } });
      fireEvent.keyDown(input, { key: "Enter" });

      await waitFor(() => {
        expect(screen.getByText("Dataset name must not be empty")).toBeInTheDocument();
      });

      expect(api.updateDataset).not.toHaveBeenCalled();
    });

    it("shows validation error for name with special characters", async () => {
      mockWorkspaceData();
      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTitle("Click to rename dataset"));

      const input = screen.getByDisplayValue("Leave Application Report");
      fireEvent.change(input, { target: { value: "Payroll@2024!" } });
      fireEvent.keyDown(input, { key: "Enter" });

      await waitFor(() => {
        expect(screen.getByText(/Only letters, digits, spaces, hyphens, and underscores are allowed/)).toBeInTheDocument();
      });

      expect(api.updateDataset).not.toHaveBeenCalled();
    });

    it("cancels edit on Escape", async () => {
      mockWorkspaceData();
      render(<DatasetWorkspaceContent datasetId="dataset-1" />);

      await waitFor(() => {
        expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByTitle("Click to rename dataset"));

      const input = screen.getByDisplayValue("Leave Application Report");
      fireEvent.keyDown(input, { key: "Escape" });

      await waitFor(() => {
        expect(screen.queryByDisplayValue("Leave Application Report")).not.toBeInTheDocument();
      });

      expect(screen.getByText("Leave Application Report")).toBeInTheDocument();
      expect(api.updateDataset).not.toHaveBeenCalled();
    });
  });

  it("shows the real schema types in the Schema tab", async () => {
    mockWorkspaceData();
    mock_search_params = new URLSearchParams("tab=Schema");

    render(<DatasetWorkspaceContent datasetId="dataset-1" />);

    await waitFor(() => {
      expect(screen.getByText("id")).toBeInTheDocument();
    });

    expect(screen.getByText("integer")).toBeInTheDocument();
    expect(screen.getByText("datetime")).toBeInTheDocument();
    expect(screen.getByText("string")).toBeInTheDocument();
    expect(screen.queryByText("text")).not.toBeInTheDocument();
    expect(semanticApi.fetchDatasetVersionSchema).toHaveBeenCalledWith("dataset-1", "version-1");
  });
});
