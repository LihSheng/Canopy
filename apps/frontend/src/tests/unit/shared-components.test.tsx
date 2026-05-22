import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { StaleIndicator } from "@/components/shared/stale-indicator";
import { ConfirmDialog } from "@/components/shared/confirm-dialog";

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

describe("ConfirmDialog", () => {
  it("renders when open", () => {
    render(
      <ConfirmDialog open title="Are you sure?" onConfirm={vi.fn()} onClose={vi.fn()} />,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Are you sure?")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <ConfirmDialog open={false} title="Hidden" onConfirm={vi.fn()} onClose={vi.fn()} />,
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("calls onConfirm when confirm button clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmDialog open title="Sure?" onConfirm={onConfirm} onClose={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });

  it("calls onClose when cancel button clicked", () => {
    const onClose = vi.fn();
    render(
      <ConfirmDialog open title="Sure?" onConfirm={vi.fn()} onClose={onClose} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls onClose on backdrop click", () => {
    const onClose = vi.fn();
    render(
      <ConfirmDialog open title="Sure?" onConfirm={vi.fn()} onClose={onClose} />,
    );
    // Click the backdrop (the outermost div with role="dialog")
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("shows custom button labels", () => {
    render(
      <ConfirmDialog
        open
        title="Remove item?"
        confirmLabel="Yes, remove"
        cancelLabel="Go back"
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Yes, remove" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Go back" })).toBeInTheDocument();
  });

  it("disables buttons and shows Working... when busy", () => {
    render(
      <ConfirmDialog
        open
        title="Deleting..."
        busy
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "Working..." })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
  });

  it("renders description when provided", () => {
    render(
      <ConfirmDialog
        open
        title="Delete?"
        description="Cannot be undone."
        onConfirm={vi.fn()}
        onClose={vi.fn()}
      />,
    );
    expect(screen.getByText("Cannot be undone.")).toBeInTheDocument();
  });

  it("omits description element when not provided", () => {
    const { container } = render(
      <ConfirmDialog open title="Delete?" onConfirm={vi.fn()} onClose={vi.fn()} />,
    );
    expect(
      container.querySelector("#confirm-dialog-description"),
    ).not.toBeInTheDocument();
  });

  it("does not call onClose on backdrop click when busy", () => {
    const onClose = vi.fn();
    render(
      <ConfirmDialog
        open
        title="Sure?"
        busy
        onConfirm={vi.fn()}
        onClose={onClose}
      />,
    );
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).not.toHaveBeenCalled();
  });
});
