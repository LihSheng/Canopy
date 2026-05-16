import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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

import { ReportPresetGrid } from "@/components/reports-v2/report-preset-grid";
import { ReportHistoryRow } from "@/components/reports-v2/report-history-row";
import { ReportHistoryList } from "@/components/reports-v2/report-history-list";
import { EXPORT_PRESETS } from "@/components/reports-v2/report-mappers";
import type { ExportHistoryItem } from "@/components/reports-v2/report-mappers";

const mockCompletedItem: ExportHistoryItem = {
  id: "exp-001",
  presetName: "Executive Summary",
  status: "completed",
  createdAt: new Date("2026-05-16T10:00:00Z"),
  timeRange: "this_month",
  snapshotTimestamp: "2026-05-16T10:30:00Z",
  errorSummary: null,
  downloadUrl: "/api/exports/jobs/exp-001/download",
};

const mockFailedItem: ExportHistoryItem = {
  id: "exp-002",
  presetName: "Department Spend",
  status: "failed",
  createdAt: new Date("2026-05-16T09:00:00Z"),
  timeRange: "last_3_months",
  snapshotTimestamp: null,
  errorSummary: "Database connection refused",
  downloadUrl: null,
};

const mockRunningItem: ExportHistoryItem = {
  id: "exp-003",
  presetName: "Anomaly Review",
  status: "running",
  createdAt: new Date("2026-05-16T11:00:00Z"),
  timeRange: "last_12_months",
  snapshotTimestamp: null,
  errorSummary: null,
  downloadUrl: null,
};

const mockQueuedItem: ExportHistoryItem = {
  id: "exp-004",
  presetName: "Executive Summary",
  status: "queued",
  createdAt: null,
  timeRange: "this_month",
  snapshotTimestamp: null,
  errorSummary: null,
  downloadUrl: null,
};

describe("ReportPresetGrid", () => {
  it("renders all three preset buttons", () => {
    render(<ReportPresetGrid presets={EXPORT_PRESETS} onTrigger={vi.fn()} exporting={null} />);

    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(screen.getByText("Department Spend")).toBeInTheDocument();
    expect(screen.getByText("Anomaly Review")).toBeInTheDocument();
  });

  it("calls onTrigger when a preset is clicked", () => {
    const onTrigger = vi.fn();
    render(<ReportPresetGrid presets={EXPORT_PRESETS} onTrigger={onTrigger} exporting={null} />);

    fireEvent.click(screen.getByText("Executive Summary"));
    expect(onTrigger).toHaveBeenCalledWith("executive_summary");
  });

  it("calls onTrigger with correct key for each preset", () => {
    const onTrigger = vi.fn();
    render(<ReportPresetGrid presets={EXPORT_PRESETS} onTrigger={onTrigger} exporting={null} />);

    fireEvent.click(screen.getByText("Department Spend"));
    expect(onTrigger).toHaveBeenCalledWith("department_spend");

    fireEvent.click(screen.getByText("Anomaly Review"));
    expect(onTrigger).toHaveBeenCalledWith("anomaly_review");
  });

  it("shows generating spinner when exporting matches preset", () => {
    render(<ReportPresetGrid presets={EXPORT_PRESETS} onTrigger={vi.fn()} exporting="executive_summary" />);

    expect(screen.getByText("Generating...")).toBeInTheDocument();
  });

  it("disables buttons when busy", () => {
    render(<ReportPresetGrid presets={EXPORT_PRESETS} onTrigger={vi.fn()} exporting="executive_summary" />);

    const buttons = screen.getAllByRole("button");
    const busyButton = buttons.find((b) => b.textContent?.includes("Executive Summary"));
    expect(busyButton).toBeDisabled();
  });
});

describe("ReportHistoryRow", () => {
  it("renders completed row with download and run again actions", () => {
    render(<ReportHistoryRow item={mockCompletedItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("Download")).toBeInTheDocument();
    expect(screen.getByText("Run again")).toBeInTheDocument();
  });

  it("renders failed row with view details button", () => {
    render(<ReportHistoryRow item={mockFailedItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Department Spend")).toBeInTheDocument();
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("View details")).toBeInTheDocument();
  });

  it("shows error details when view details clicked", () => {
    render(<ReportHistoryRow item={mockFailedItem} onRerun={vi.fn()} exporting={null} />);

    fireEvent.click(screen.getByText("View details"));

    expect(screen.getByText("Error details")).toBeInTheDocument();
    expect(screen.getByText("Database connection refused")).toBeInTheDocument();
    expect(screen.getByText("Hide details")).toBeInTheDocument();
  });

  it("toggles error details visibility", () => {
    render(<ReportHistoryRow item={mockFailedItem} onRerun={vi.fn()} exporting={null} />);

    fireEvent.click(screen.getByText("View details"));
    expect(screen.getByText("Database connection refused")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Hide details"));
    expect(screen.queryByText("Database connection refused")).not.toBeInTheDocument();
  });

  it("renders running row with spinner", () => {
    render(<ReportHistoryRow item={mockRunningItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Anomaly Review")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.queryByText("Download")).not.toBeInTheDocument();
    expect(screen.queryByText("Run again")).not.toBeInTheDocument();
  });

  it("renders queued row without action buttons", () => {
    render(<ReportHistoryRow item={mockQueuedItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it("shows snapshot timestamp on completed row", () => {
    render(<ReportHistoryRow item={mockCompletedItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText(/Snapshot:/)).toBeInTheDocument();
  });

  it("does not show snapshot timestamp on failed row", () => {
    render(<ReportHistoryRow item={mockFailedItem} onRerun={vi.fn()} exporting={null} />);

    expect(screen.queryByText(/Snapshot:/)).not.toBeInTheDocument();
  });

  it("calls onRerun when Run again clicked", () => {
    const onRerun = vi.fn();
    render(<ReportHistoryRow item={mockCompletedItem} onRerun={onRerun} exporting={null} />);

    fireEvent.click(screen.getByText("Run again"));
    expect(onRerun).toHaveBeenCalledWith("exp-001");
  });

  it("disables Run again when currently exporting that item", () => {
    render(<ReportHistoryRow item={mockCompletedItem} onRerun={vi.fn()} exporting="exp-001" />);

    const btn = screen.getByText("Run again");
    expect(btn).toBeDisabled();
  });
});

describe("ReportHistoryList", () => {
  it("renders empty state when no items", () => {
    render(<ReportHistoryList items={[]} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText(/No recent exports/)).toBeInTheDocument();
  });

  it("renders all history rows", () => {
    const items = [mockCompletedItem, mockFailedItem];
    render(<ReportHistoryList items={items} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Executive Summary")).toBeInTheDocument();
    expect(screen.getByText("Department Spend")).toBeInTheDocument();
  });

  it("renders section title", () => {
    render(<ReportHistoryList items={[mockCompletedItem]} onRerun={vi.fn()} exporting={null} />);

    expect(screen.getByText("Recent exports")).toBeInTheDocument();
  });
});
