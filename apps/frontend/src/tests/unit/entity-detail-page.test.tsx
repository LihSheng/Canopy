import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EntityDetailPage } from "@/app/dashboard/entities/[id]/page";

const mockFetchEntity = vi.fn();
const mockFetchEntityStatus = vi.fn();
const mockFetchSourceBindings = vi.fn();
const mockPublishDraft = vi.fn();
const mockFetchDataset = vi.fn();
const mockFetchDatasetVersions = vi.fn();

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "entity-1" }),
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
  }),
}));

vi.mock("@/lib/api/entities", () => ({
  fetchEntity: (...args: unknown[]) => mockFetchEntity(...args),
  fetchEntityStatus: (...args: unknown[]) => mockFetchEntityStatus(...args),
  forkDraft: vi.fn(),
  createInitialRevision: vi.fn(),
  publishDraft: (...args: unknown[]) => mockPublishDraft(...args),
  discardDraft: vi.fn(),
  addProperty: vi.fn(),
  updateProperty: vi.fn(),
  removeProperty: vi.fn(),
  reorderProperties: vi.fn(),
  fetchSourceBindings: (...args: unknown[]) => mockFetchSourceBindings(...args),
  setSourceBindings: vi.fn(),
  updateDraft: vi.fn(),
}));

vi.mock("@/lib/api/data-source", () => ({
  fetchDataset: (...args: unknown[]) => mockFetchDataset(...args),
  fetchDatasetVersions: (...args: unknown[]) => mockFetchDatasetVersions(...args),
}));

vi.mock("@/components/analytics-shell/analytics-page-shell", () => ({
  AnalyticsPageShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/shared", async () => {
  const actual = await vi.importActual<typeof import("@/components/shared")>("@/components/shared");
  return {
    ...actual,
    LoadingSpinner: () => <div>Loading...</div>,
    ErrorState: ({ message }: { message: string }) => <div>{message}</div>,
  };
});

vi.mock("@/components/entity-graph/property-editor", () => ({
  PropertyEditor: () => <div data-testid="property-editor" />,
}));

vi.mock("@/components/entity-graph/entity-graph-tab", () => ({
  EntityGraphTab: () => <div data-testid="entity-graph-tab">EntityGraphTab Canvas</div>,
}));

const baseEntity = {
  id: "entity-1",
  object_type_key: "employee",
  display_name: "Employee",
  description: "Employee entity",
  created_at: "2026-06-01T00:00:00Z",
  updated_at: "2026-06-01T00:00:00Z",
  dataset_name: "Payroll",
  dataset_id: "dataset-1",
  project_id: "project-1",
  mapping: null,
  has_published_revision: false,
  has_draft: true,
  draft_lock_holder_id: null,
  published_revision_number: null,
  draft_revision_number: 1,
  published_revision: null,
  draft_revision: {
    id: "rev-1",
    revision_number: 1,
    status: "draft",
    properties: [],
    source_nodes: [],
    links: [],
    computed_properties: [],
    layout_state: {},
    published_at: null,
  },
};

describe("EntityDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchEntity.mockResolvedValue(baseEntity);
    mockFetchEntityStatus.mockResolvedValue({
      has_published: false,
      has_draft: true,
      lock_holder_id: null,
      published_revision_number: null,
      draft_revision_number: 1,
      published_at: null,
    });
    mockFetchSourceBindings.mockResolvedValue([]);
    mockFetchDataset.mockResolvedValue({
      id: "dataset-1",
      project_id: "project-1",
      connection_id: "conn-1",
      name: "Payroll",
      source_object_name: "payroll",
      status: "active",
      active_version_id: "version-1",
      created_at: "2026-06-01T00:00:00Z",
      updated_at: "2026-06-01T00:00:00Z",
    });
    mockFetchDatasetVersions.mockResolvedValue([
      {
        id: "version-1",
        dataset_id: "dataset-1",
        run_id: "run-1",
        version_number: 1,
        status: "ready",
        row_count: 100,
        column_count: 5,
        storage_path: "/tmp",
        cleaning_issues: [],
        created_at: "2026-06-01T00:00:00Z",
      },
    ]);
    mockPublishDraft.mockResolvedValue({ ...baseEntity.draft_revision, status: "published" });
  });

  it("renders the entity canvas in Entity Manager", async () => {
    render(<EntityDetailPage />);

    await waitFor(() => {
      expect(screen.getByTestId("entity-graph-tab")).toBeInTheDocument();
    });
  });

  it("shows a fallback note when the backing dataset is missing", async () => {
    mockFetchDataset.mockRejectedValueOnce(new Error("Dataset not found"));

    render(<EntityDetailPage />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Canvas unavailable. The entity mapping is loaded, but the backing dataset record cannot be found."
        )
      ).toBeInTheDocument();
    });

    expect(screen.queryByText("Dataset not found")).not.toBeInTheDocument();
    expect(screen.queryByTestId("entity-graph-tab")).not.toBeInTheDocument();
  });

  it("sends the dataset dependency when publishing", async () => {
    render(<EntityDetailPage />);

    await waitFor(() => {
      expect(screen.getByText("Publish")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Publish"));

    await waitFor(() => {
      expect(mockPublishDraft).toHaveBeenCalledWith("entity-1", [
        {
          dependency_type: "dataset",
          dependency_id: "dataset-1",
        },
      ]);
    });
  });
});
