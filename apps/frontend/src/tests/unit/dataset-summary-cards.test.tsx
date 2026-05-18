import { render } from "@testing-library/react";
import { screen } from "@testing-library/dom";
import { describe, expect, it } from "vitest";

import { DatasetSummaryCards } from "@/components/dataset-summary-cards";

const mockHealth = {
  dataset_id: "ds-1",
  row_count: 15234,
  column_count: 8,
  missing_required_mappings: false,
  warning_count: 2,
  last_run_status: "completed",
  last_published_version: 3,
  freshness_at: "2026-05-18T10:30:00Z",
};

const mockHealthFailed = {
  dataset_id: "ds-2",
  row_count: 0,
  column_count: 3,
  missing_required_mappings: true,
  warning_count: 5,
  last_run_status: "failed",
  last_published_version: null,
  freshness_at: null,
};

describe("DatasetSummaryCards", () => {
  it("renders row count, column count, version, and last run status", () => {
    render(
      <DatasetSummaryCards
        health={mockHealth}
        versionCount={5}
        activeVersionNumber={3}
      />,
    );

    expect(screen.getByText("Row Count")).toBeInTheDocument();
    expect(screen.getByText("15,234")).toBeInTheDocument();
    expect(screen.getByText("Column Count")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("Version")).toBeInTheDocument();
    expect(screen.getByText("v3 (of 5)")).toBeInTheDocument();
    expect(screen.getByText("Last Run")).toBeInTheDocument();
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("renders freshness timestamp when available", () => {
    render(
      <DatasetSummaryCards
        health={mockHealth}
        versionCount={1}
        activeVersionNumber={1}
      />,
    );

    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("renders fallback values when health is null", () => {
    render(
      <DatasetSummaryCards
        health={null}
        versionCount={0}
        activeVersionNumber={undefined}
      />,
    );

    const dashes = screen.getAllByText("--");
    expect(dashes.length).toBe(4);
  });

  it("renders failed run status badge with correct styling", () => {
    render(
      <DatasetSummaryCards
        health={mockHealthFailed}
        versionCount={2}
        activeVersionNumber={1}
      />,
    );

    expect(screen.getByText("failed")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders version display without active version", () => {
    render(
      <DatasetSummaryCards
        health={mockHealth}
        versionCount={4}
        activeVersionNumber={undefined}
      />,
    );

    expect(screen.getByText("--")).toBeInTheDocument();
  });
});
