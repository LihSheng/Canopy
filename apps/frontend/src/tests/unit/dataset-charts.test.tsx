import { render } from "@testing-library/react";
import { screen } from "@testing-library/dom";
import { describe, expect, it } from "vitest";

import { DatasetCharts } from "@/components/dataset-charts";

const columns = ["name", "age", "city", "score"];
const rows: (string | number | null)[][] = [
  ["Alice", 30, "NYC", 95.5],
  ["Bob", 25, "LA", 88.0],
  ["Charlie", 35, "SF", 92.3],
];

describe("DatasetCharts", () => {
  it("renders column type distribution chart with columns and rows", () => {
    render(
      <DatasetCharts
        columns={columns}
        rows={rows}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("Column Type Distribution")).toBeInTheDocument();
    expect(screen.getByText("Row Count")).toBeInTheDocument();
    expect(screen.getByText("Numeric")).toBeInTheDocument();
    expect(screen.getByText("Text")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders loading state", () => {
    render(
      <DatasetCharts
        columns={[]}
        rows={[]}
        loading={true}
        error={null}
      />,
    );

    expect(screen.getByText("Loading charts...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    render(
      <DatasetCharts
        columns={[]}
        rows={[]}
        loading={false}
        error="Failed to load"
      />,
    );

    expect(screen.getByText("Failed to load")).toBeInTheDocument();
  });

  it("renders empty state when there are no columns", () => {
    render(
      <DatasetCharts
        columns={[]}
        rows={[]}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("No data")).toBeInTheDocument();
    expect(screen.getByText("No columns to chart.")).toBeInTheDocument();
  });

  it("shows row count from current window", () => {
    render(
      <DatasetCharts
        columns={columns}
        rows={rows}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText("rows in current preview window")).toBeInTheDocument();
  });

  it("classifies columns deterministically", () => {
    const numericCols = ["x", "y", "z"];
    const numericRows: (string | number | null)[][] = [
      [10, 20, 30],
      [40, 50, 60],
    ];

    render(
      <DatasetCharts
        columns={numericCols}
        rows={numericRows}
        loading={false}
        error={null}
      />,
    );

    expect(screen.getByText(/Numeric/)).toBeInTheDocument();
    expect(screen.getByText(/Text/)).toBeInTheDocument();
  });
});
