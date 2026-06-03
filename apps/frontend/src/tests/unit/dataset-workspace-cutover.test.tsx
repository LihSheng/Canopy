import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import DatasetWorkspaceContent from "@/app/dashboard/connections/datasets/[id]/dataset-workspace-content";
import type { Dataset, DatasetVersion } from "@/lib/api/types";

// ─── Mocks ───

const mockFlags = vi.fn<() => Record<string, boolean>>();
vi.mock("@/lib/feature-flags-context", () => ({
  useFeatureFlags: () => ({
    flags: mockFlags(),
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}));

// Use a mutable search params that the test controls
let _searchParams = new URLSearchParams("");
const mockRouterReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useSearchParams: () => _searchParams,
  useRouter: () => ({ replace: mockRouterReplace }),
}));

// Mock API modules
vi.mock("@/lib/api/data-source", () => ({
  fetchDataset: vi.fn().mockResolvedValue(null),
  fetchDatasetDeleteSummary: vi.fn().mockResolvedValue(null),
  fetchDatasetPreview: vi.fn().mockResolvedValue(null),
  fetchDatasetVersions: vi.fn().mockResolvedValue([]),
  fetchDatasetHealth: vi.fn().mockResolvedValue(null),
  fetchDatasetLineage: vi.fn().mockResolvedValue(null),
  fetchRuns: vi.fn().mockResolvedValue([]),
  fetchConnection: vi.fn().mockResolvedValue(null),
  fetchRetentionPolicy: vi.fn().mockResolvedValue(null),
}));

vi.mock("@/lib/api/semantic", () => ({
  fetchDatasetVersionSchema: vi.fn().mockResolvedValue([]),
}));

// Mock dataset components
vi.mock("@/components/dataset-preview-grid", () => ({
  DatasetPreviewGrid: () => <div data-testid="preview-grid" />,
}));
vi.mock("@/components/dataset-summary-cards", () => ({
  DatasetSummaryCards: () => <div data-testid="summary-cards" />,
}));
vi.mock("@/components/dataset-charts", () => ({
  DatasetCharts: () => <div data-testid="dataset-charts" />,
}));
vi.mock("@/components/version-history", () => ({
  VersionHistory: () => <div data-testid="version-history" />,
}));
vi.mock("@/components/health-panel", () => ({
  HealthPanel: () => <div data-testid="health-panel" />,
}));
vi.mock("@/components/run-history", () => ({
  RunHistory: () => <div data-testid="run-history" />,
}));
vi.mock("@/components/lineage-view", () => ({
  LineageView: () => <div data-testid="lineage-view" />,
}));
vi.mock("@/components/data-studio/sync-policy-editor", () => ({
  SyncPolicyEditor: () => <div data-testid="sync-policy-editor" />,
}));

// Mock EntityTab (old wizard)
vi.mock("@/components/entity-mapping/entity-tab", () => ({
  EntityTab: () => <div data-testid="entity-tab-wizard">EntityTab Wizard</div>,
}));

// Mock EntityGraphTab (canvas)
vi.mock("@/components/entity-graph/entity-graph-tab", () => ({
  EntityGraphTab: () => <div data-testid="entity-graph-tab">EntityGraphTab Canvas</div>,
}));

// Mock useToast by wrapping in ToastProvider
const MockToastProvider = ({ children }: { children: React.ReactNode }) => <>{children}</>;
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

// ─── Fixtures ───

const baseVersion: DatasetVersion = {
  id: "version-1",
  dataset_id: "ds-1",
  run_id: "run-1",
  version_number: 1,
  status: "ready",
  row_count: 0,
  column_count: 0,
  storage_path: "",
  cleaning_issues: [],
  created_at: "2026-01-01T00:00:00Z",
};

const baseDataset: Dataset = {
  id: "ds-1",
  project_id: "proj-1",
  connection_id: "conn-1",
  name: "Test Dataset",
  source_object_name: "test_table",
  status: "active",
  active_version_id: null,
  sync_mode: "batch",
  batch_strategy: "full_snapshot",
  real_time_strategy: null,
  cursor_column: null,
  last_cursor_value: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

// ─── Tests ───

describe("DatasetWorkspaceContent — Canvas Cutover", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _searchParams = new URLSearchParams("");
  });

  describe("when entity_canvas_enabled flag is ON", () => {
    beforeEach(() => {
      mockFlags.mockReturnValue({ entity_canvas_enabled: true });
    });

    it("does not show a separate 'Graph' tab", async () => {
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByText("Entity")).toBeInTheDocument();
      });

      // Graph tab should not be visible when canvas is primary
      expect(screen.queryByText("Graph")).not.toBeInTheDocument();
    });

    it("renders EntityGraphTab (canvas) when Entity tab is active", async () => {
      _searchParams = new URLSearchParams("tab=Entity");
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByTestId("entity-graph-tab")).toBeInTheDocument();
      });

      expect(screen.queryByTestId("entity-tab-wizard")).not.toBeInTheDocument();
    });

    it("shows base tabs plus Entity (no Graph)", async () => {
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByText("Overview")).toBeInTheDocument();
        expect(screen.getByText("Preview")).toBeInTheDocument();
        expect(screen.getByText("Schema")).toBeInTheDocument();
        expect(screen.getByText("Transform")).toBeInTheDocument();
        expect(screen.getByText("Lineage")).toBeInTheDocument();
        expect(screen.getByText("Runs")).toBeInTheDocument();
        expect(screen.getByText("Versions")).toBeInTheDocument();
        expect(screen.getByText("Details")).toBeInTheDocument();
        expect(screen.getByText("Entity")).toBeInTheDocument();
      });

      expect(screen.queryByText("Graph")).not.toBeInTheDocument();
    });

    it("redirects Graph tab URL to Entity when canvas is primary", async () => {
      _searchParams = new URLSearchParams("tab=Graph");
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      // The redirect useEffect should fire and replace URL
      await waitFor(() => {
        expect(mockRouterReplace).toHaveBeenCalled();
      });

      // It should redirect to Entity tab
      const lastCall = mockRouterReplace.mock.calls.at(-1)?.[0] as string;
      expect(lastCall).toContain("tab=Entity");
    });
  });

  describe("when entity_canvas_enabled flag is OFF (fallback)", () => {
    beforeEach(() => {
      mockFlags.mockReturnValue({ entity_canvas_enabled: false });
    });

    it("shows both 'Entity' and 'Graph' tabs", async () => {
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByText("Entity")).toBeInTheDocument();
        expect(screen.getByText("Graph")).toBeInTheDocument();
      });
    });

    it("renders EntityTab (wizard) when Entity tab is active", async () => {
      _searchParams = new URLSearchParams("tab=Entity");
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByTestId("entity-tab-wizard")).toBeInTheDocument();
        expect(screen.queryByTestId("entity-graph-tab")).not.toBeInTheDocument();
      });
    });

    it("renders EntityGraphTab (canvas) when Graph tab is active", async () => {
      _searchParams = new URLSearchParams("tab=Graph");
      const { fetchDataset } = await import("@/lib/api/data-source");
      vi.mocked(fetchDataset).mockResolvedValue(baseDataset);

      render(<DatasetWorkspaceContent datasetId="ds-1" />);

      await waitFor(() => {
        expect(screen.getByTestId("entity-graph-tab")).toBeInTheDocument();
      });
    });
  });
});
