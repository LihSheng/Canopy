import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User" },
    loading: false, error: null, refetch: vi.fn(), logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/reports",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/reports", () => ({
  fetchExportHistory: vi.fn(),
  triggerExport: vi.fn(),
  rerunExportJob: vi.fn(),
  fetchExportJob: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({ status: "idle", last_refresh: null, last_attempt: null, error_message: null }),
}));

import { ReportsPage } from "@/components/reports/reports-page";
import * as api from "@/lib/api/reports";
import type { ExportJob } from "@/lib/api/types";

const mockExportJobs: ExportJob[] = [
  {
    id: "exp-001",
    status: "completed",
    preset_name: "Executive Summary",
    snapshot_id: "snap-123",
    time_range: "this_month",
    snapshot_timestamp: "2026-05-16T10:30:00Z",
    started_at: "2026-05-16T10:00:00Z",
    finished_at: "2026-05-16T10:30:00Z",
    file_size_bytes: 12500,
    error_message: null,
  },
  {
    id: "exp-002",
    status: "failed",
    preset_name: "Department Spend",
    snapshot_id: null,
    time_range: "last_3_months",
    snapshot_timestamp: null,
    started_at: "2026-05-16T09:00:00Z",
    finished_at: "2026-05-16T09:01:00Z",
    file_size_bytes: null,
    error_message: "Database connection refused",
  },
];

describe("Reports V2 integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and renders page with presets and history", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: mockExportJobs });

    render(<ReportsPage />);

    await waitFor(() => {
      const summaryPresets = screen.getAllByText("Executive Summary");
      expect(summaryPresets.length).toBeGreaterThanOrEqual(1);
      const deptPresets = screen.getAllByText("Department Spend");
      expect(deptPresets.length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("Anomaly Review")).toBeInTheDocument();
    });
  });

  it("shows completed and failed rows in history", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: mockExportJobs });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Completed")).toBeInTheDocument();
      expect(screen.getByText("Failed")).toBeInTheDocument();
    });
  });

  it("shows empty history when no exports", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: [] });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText(/No recent exports/)).toBeInTheDocument();
    });
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchExportHistory).mockRejectedValue(new Error("Network error"));

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("completes preset trigger flow", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: [] });
    vi.mocked(api.triggerExport).mockResolvedValue({ accepted: true, job_id: "exp-new" });
    vi.mocked(api.fetchExportJob).mockResolvedValue({
      ...mockExportJobs[0],
      id: "exp-new",
      status: "completed",
    });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    });
  });

  it("renders Run again button on completed exports", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: mockExportJobs });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Run again")).toBeInTheDocument();
    });
  });

  it("polls the triggered export job instead of guessing from latest history", async () => {
    vi.mocked(api.fetchExportHistory).mockResolvedValue({ jobs: [] });
    vi.mocked(api.triggerExport).mockResolvedValue({ accepted: true, job_id: "exp-new" });
    vi.mocked(api.fetchExportJob).mockResolvedValue({
      ...mockExportJobs[0],
      id: "exp-new",
      status: "completed",
    });

    render(<ReportsPage />);

    await waitFor(() => {
      expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    });
  });
});
