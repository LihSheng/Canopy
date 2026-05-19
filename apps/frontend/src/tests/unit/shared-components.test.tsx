import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StaleIndicator } from "@/components/shared/stale-indicator";

describe("LoadingSpinner", () => {
  it("renders default text", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("renders custom text", () => {
    render(<LoadingSpinner text="Fetching data..." />);
    expect(screen.getByText("Fetching data...")).toBeInTheDocument();
  });

  it("has status role", () => {
    render(<LoadingSpinner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});

describe("EmptyState", () => {
  it("renders default title", () => {
    render(<EmptyState />);
    expect(screen.getByText("No data available")).toBeInTheDocument();
  });

  it("renders custom title and description", () => {
    render(<EmptyState title="Nothing here" description="Check back later" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Check back later")).toBeInTheDocument();
  });

  it("renders minimal variant without notice banner styling", () => {
    render(<EmptyState variant="minimal" title="No data" description="Check back later" />);
    expect(screen.getByText("No data")).toBeInTheDocument();
    expect(screen.getByText("Check back later")).toBeInTheDocument();
  });
});

describe("ErrorState", () => {
  it("renders error message", () => {
    render(<ErrorState message="Something broke" />);
    expect(screen.getByText("Something broke")).toBeInTheDocument();
  });

  it("renders retry button when onRetry provided", () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Failed" onRetry={onRetry} />);
    const btn = screen.getByText("Try again");
    expect(btn).toBeInTheDocument();
    fireEvent.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("does not render retry button when onRetry not provided", () => {
    render(<ErrorState message="Failed" />);
    expect(screen.queryByText("Try again")).not.toBeInTheDocument();
  });
});

describe("StaleIndicator", () => {
  it("renders formatted date", () => {
    render(<StaleIndicator lastUpdated="2024-01-15T08:30:00Z" />);
    expect(screen.getByText(/Data as of/)).toBeInTheDocument();
  });

  it("renders nothing when no date", () => {
    const { container } = render(<StaleIndicator lastUpdated={undefined} />);
    expect(container.firstChild).toBeNull();
  });
});
