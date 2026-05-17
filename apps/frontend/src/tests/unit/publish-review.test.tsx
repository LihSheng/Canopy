import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { PublishReview } from "@/components/ingestion-v2/publish-review";

const mockFetchCleanedSnapshot = vi.fn();
const mockFetchMappings = vi.fn();
const mockFetchPublishState = vi.fn();
const mockFetchPublishHistory = vi.fn();
const mockPublishUpload = vi.fn();

vi.mock("@/lib/api/ingestion", () => ({
  fetchCleanedSnapshot: (...args: unknown[]) => mockFetchCleanedSnapshot(...args),
  fetchMappings: (...args: unknown[]) => mockFetchMappings(...args),
  fetchPublishState: (...args: unknown[]) => mockFetchPublishState(...args),
  fetchPublishHistory: (...args: unknown[]) => mockFetchPublishHistory(...args),
  publishUpload: (...args: unknown[]) => mockPublishUpload(...args),
}));

function makeSnapshot(overrides: Record<string, unknown> = {}) {
  return {
    id: "snap-1",
    upload_id: "u1",
    template_version_id: "tv-1",
    status: "completed",
    row_count: 10,
    warning_count: 0,
    warnings: [],
    created_at: "2025-01-15T00:00:00Z",
    ...overrides,
  };
}

function makeMappings(confirmedCount: number, total: number = 3) {
  const decisions = [];
  for (let i = 0; i < total; i++) {
    decisions.push({
      source_column_name: `col_${i}`,
      target_field_name: `field_${i}`,
      confirmed: i < confirmedCount,
      overridden_by_user: false,
    });
  }
  return {
    upload_id: "u1",
    decisions,
    column_profiles: [],
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  mockFetchCleanedSnapshot.mockResolvedValue(makeSnapshot());
  mockFetchMappings.mockResolvedValue(makeMappings(3));
  mockFetchPublishState.mockResolvedValue(null);
  mockFetchPublishHistory.mockResolvedValue({ records: [] });
});

describe("PublishReview", () => {
  it("renders loading state initially", () => {
    mockFetchCleanedSnapshot.mockReturnValue(new Promise(() => {}));
    mockFetchMappings.mockReturnValue(new Promise(() => {}));
    render(<PublishReview uploadId="u1" />);
    const spinner = document.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("renders validation checks with pass state", async () => {
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("Mapping decisions confirmed")).toBeInTheDocument();
    });

    expect(screen.getByText("Non-empty result")).toBeInTheDocument();
    expect(screen.getByText("Cleaned snapshot status")).toBeInTheDocument();
  });

  it("displays publish button when no active publish", async () => {
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("Publish")).toBeInTheDocument();
    });
  });

  it("shows blocking error with missing mappings", async () => {
    mockFetchMappings.mockResolvedValue(makeMappings(0));
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      const buttons = screen.getAllByText("Publish");
      const publishBtn = buttons[0] as HTMLButtonElement;
      expect(publishBtn.disabled).toBe(true);
    });
  });

  it("disables publish button when snapshot has zero rows", async () => {
    mockFetchCleanedSnapshot.mockResolvedValue(makeSnapshot({ row_count: 0 }));
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      const buttons = screen.getAllByText("Publish");
      const publishBtn = buttons[0] as HTMLButtonElement;
      expect(publishBtn.disabled).toBe(true);
    });
  });

  it("shows warning state for snapshots with warnings", async () => {
    mockFetchCleanedSnapshot.mockResolvedValue(
      makeSnapshot({ status: "completed_with_warnings", warning_count: 3 }),
    );
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText(/Completed with 3 warnings/)).toBeInTheDocument();
    });
  });

  it("shows published state when active publish exists", async () => {
    mockFetchPublishState.mockResolvedValue({
      id: "pub-1",
      upload_id: "u1",
      cleaned_snapshot_id: "snap-1",
      template_version_id: "tv-1",
      status: "active",
      published_at: "2025-01-15T12:00:00Z",
      published_by: null,
      validation_errors: [],
      validation_warnings: [],
      created_at: "2025-01-15T12:00:00Z",
    });

    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText(/version is active/)).toBeInTheDocument();
    });
  });

  it("renders history list when records exist", async () => {
    mockFetchPublishHistory.mockResolvedValue({
      records: [
        {
          id: "pub-1",
          upload_id: "u1",
          cleaned_snapshot_id: "snap-1",
          template_version_id: "tv-1",
          status: "active",
          published_at: "2025-01-15T12:00:00Z",
          published_by: null,
          validation_errors: [],
          validation_warnings: [],
          created_at: "2025-01-15T12:00:00Z",
        },
      ],
    });

    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("Publish History")).toBeInTheDocument();
      expect(screen.getByText("active")).toBeInTheDocument();
    });
  });

  it("shows error state for failed snapshot", async () => {
    mockFetchCleanedSnapshot.mockResolvedValue(
      makeSnapshot({ status: "failed", row_count: 0, warning_count: 0 }),
    );
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      const buttons = screen.getAllByText("Publish");
      const publishBtn = buttons[0] as HTMLButtonElement;
      expect(publishBtn.disabled).toBe(true);
    });
  });

  it("shows error for zero rows", async () => {
    mockFetchCleanedSnapshot.mockResolvedValue(makeSnapshot({ row_count: 0 }));
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("Zero rows in cleaned output")).toBeInTheDocument();
    });
  });

  it("renders summary section with row count", async () => {
    render(<PublishReview uploadId="u1" />);

    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
    });
  });
});
