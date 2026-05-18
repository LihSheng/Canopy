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
});
