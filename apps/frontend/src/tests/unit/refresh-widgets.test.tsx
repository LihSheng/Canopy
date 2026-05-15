import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RefreshStatusBadge, RefreshTimelinePanel } from "@/components/dashboard/refresh-widgets";

describe("RefreshStatusBadge", () => {
  it('renders "Up to date" for idle status', () => {
    render(<RefreshStatusBadge status="idle" />);
    expect(screen.getByText("Up to date")).toBeInTheDocument();
  });

  it('renders "Queued" for queued status', () => {
    render(<RefreshStatusBadge status="queued" />);
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it('renders "Refreshing..." for running status', () => {
    render(<RefreshStatusBadge status="running" />);
    expect(screen.getByText("Refreshing...")).toBeInTheDocument();
  });

  it('renders "Completed" for completed status', () => {
    render(<RefreshStatusBadge status="completed" />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it('renders "Failed" for failed status', () => {
    render(<RefreshStatusBadge status="failed" />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });
});

describe("RefreshTimelinePanel", () => {
  it("renders last refresh time", () => {
    render(<RefreshTimelinePanel lastRefresh="2024-06-15T10:30:00Z" lastAttempt={null} />);
    expect(screen.getByText(/Last refresh:/)).toBeInTheDocument();
    expect(screen.getByText(/Jun 15/)).toBeInTheDocument();
  });

  it("renders last attempt when different from last refresh", () => {
    render(
      <RefreshTimelinePanel
        lastRefresh="2024-06-15T10:30:00Z"
        lastAttempt="2024-06-15T11:00:00Z"
      />,
    );
    expect(screen.getByText(/Last attempt:/)).toBeInTheDocument();
  });

  it("shows N/A when no dates", () => {
    render(<RefreshTimelinePanel lastRefresh={null} lastAttempt={null} />);
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });
});
