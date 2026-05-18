import { fireEvent, render } from "@testing-library/react";
import { screen } from "@testing-library/dom";
import { describe, expect, it, vi } from "vitest";

import { VersionHistory } from "@/components/version-history";
import type { DatasetVersion } from "@/lib/api/types";

const mockVersions: DatasetVersion[] = [
  {
    id: "v1",
    dataset_id: "ds-1",
    run_id: "run-1",
    version_number: 1,
    status: "ready",
    row_count: 15000,
    column_count: 8,
    storage_path: "/data/v1",
    cleaning_issues: [],
    created_at: "2026-05-17T10:00:00Z",
  },
  {
    id: "v2",
    dataset_id: "ds-1",
    run_id: "run-2",
    version_number: 2,
    status: "processing",
    row_count: 15200,
    column_count: 8,
    storage_path: "/data/v2",
    cleaning_issues: [
      { issue: "missing_value", column: "name", row: 42 },
      { issue: "outlier", column: "amount", row: 100 },
    ],
    created_at: "2026-05-18T08:00:00Z",
  },
  {
    id: "v3",
    dataset_id: "ds-1",
    run_id: "run-3",
    version_number: 3,
    status: "failed",
    row_count: 0,
    column_count: 0,
    storage_path: "/data/v3",
    cleaning_issues: [],
    created_at: "2026-05-18T09:00:00Z",
  },
];

describe("VersionHistory", () => {
  it("renders multiple versions in a table", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v2"
      />,
    );

    expect(screen.getByText("v1")).toBeInTheDocument();
    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(screen.getByText("v3")).toBeInTheDocument();
    expect(screen.getByText("ready")).toBeInTheDocument();
    expect(screen.getByText("processing")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
  });

  it("highlights the active version with Active label", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v2"
      />,
    );

    expect(screen.getByText("Active")).toBeInTheDocument();
  });

  it("does not show Active label for non-active versions", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v3"
      />,
    );

    const activeLabels = screen.getAllByText("Active");
    expect(activeLabels.length).toBe(1);
  });

  it("displays cleaning issue count correctly", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v1"
      />,
    );

    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("shows 0 for versions with no cleaning issues", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v1"
      />,
    );

    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBeGreaterThanOrEqual(2);
  });

  it("renders empty state when no versions exist", () => {
    render(
      <VersionHistory
        versions={[]}
        activeVersionId={null}
      />,
    );

    expect(screen.getByText("No versions yet")).toBeInTheDocument();
  });

  it("renders row and column counts", () => {
    render(
      <VersionHistory
        versions={[mockVersions[0]]}
        activeVersionId="v1"
      />,
    );

    expect(screen.getByText("15,000")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("renders version created dates", () => {
    render(
      <VersionHistory
        versions={[mockVersions[0]]}
        activeVersionId="v1"
      />,
    );

    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("renders delete version actions for non-active versions", () => {
    const onDeleteVersion = vi.fn();

    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v2"
        onDeleteVersion={onDeleteVersion}
      />,
    );

    expect(screen.getAllByRole("button", { name: "Delete Version" }).length).toBe(2);
    fireEvent.click(screen.getAllByRole("button", { name: "Delete Version" })[0]);
    expect(onDeleteVersion).toHaveBeenCalledWith(mockVersions[0]);
  });

  it("shows locked message when delete actions are enabled", () => {
    render(
      <VersionHistory
        versions={mockVersions}
        activeVersionId="v2"
        onDeleteVersion={vi.fn()}
      />,
    );

    expect(
      screen.getByText(/Active version is locked/i),
    ).toBeInTheDocument();
    expect(screen.getByText("Locked")).toBeInTheDocument();
  });
});
