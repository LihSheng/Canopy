import { render } from "@testing-library/react";
import { fireEvent, screen } from "@testing-library/dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

const data_editor_mock = vi.fn((_props: Record<string, unknown>) => {
  return <div data-testid="glide-grid" />;
});

vi.mock("@glideapps/glide-data-grid", () => ({
  DataEditor: (props: Record<string, unknown>) => data_editor_mock(props),
  GridCellKind: {
    Text: "text",
  },
}));

import { DatasetPreviewGrid } from "@/components/dataset-preview-grid";

const columns = ["name", "amount"];
const rows: (string | number | boolean | null)[][] = [
  ["Alice", 100],
  ["Bob", 200],
];

beforeEach(() => {
  data_editor_mock.mockClear();
});

describe("DatasetPreviewGrid", () => {
  it("renders loading state", () => {
    render(
      <DatasetPreviewGrid
        columns={[]}
        rows={[]}
        totalRowCount={0}
        page={1}
        pageSize={100}
        loading={true}
        error={null}
        onPageChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Loading preview data...")).toBeInTheDocument();
  });

  it("renders error state", () => {
    const onRetry = vi.fn();
    render(
      <DatasetPreviewGrid
        columns={[]}
        rows={[]}
        totalRowCount={0}
        page={1}
        pageSize={100}
        loading={false}
        error="Failed to load"
        onPageChange={vi.fn()}
        onRetry={onRetry}
      />,
    );
    expect(screen.getByText("Failed to load")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("renders empty state when there are no columns", () => {
    render(
      <DatasetPreviewGrid
        columns={[]}
        rows={[]}
        totalRowCount={0}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );
    expect(screen.getByText("No data available")).toBeInTheDocument();
    expect(screen.getByText("This dataset has no columns to display.")).toBeInTheDocument();
  });

  it("passes the dataset rows into the glide grid", () => {
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={rows}
        totalRowCount={2}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.getByTestId("glide-grid")).toBeInTheDocument();
    const grid_props = data_editor_mock.mock.calls[0][0] as {
      className: string;
      columns: Array<{ title: string; width: number }>;
      rows: number;
      rowMarkers: { kind: string; startIndex: number };
      getCellContent: (cell: readonly [number, number]) => { kind: string; displayData: string; readonly: boolean };
      showSearch: boolean;
      onSearchClose: (() => void) | undefined;
      keybindings: { search: boolean };
    };

    expect(grid_props.className).toBe("h-full w-full");
    expect(grid_props.rows).toBe(2);
    expect(grid_props.columns.map((column) => column.title)).toEqual(columns);
    expect(grid_props.columns[0].width).toBeGreaterThan(0);
    expect(grid_props.columns[1].width).toBeGreaterThan(0);
    expect(grid_props.rowMarkers).toEqual({ kind: "number", startIndex: 1 });
    expect(grid_props.getCellContent([0, 0]).displayData).toBe("Alice");
    expect(grid_props.getCellContent([1, 1]).displayData).toBe("200");
    expect(grid_props.showSearch).toBe(false);
    expect(grid_props.onSearchClose).toBeDefined();
    expect(grid_props.keybindings).toEqual({ search: true });
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("opens the search box from ctrl+f", () => {
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={rows}
        totalRowCount={2}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );

    fireEvent.keyDown(window, { key: "f", ctrlKey: true });

    const grid_props = data_editor_mock.mock.calls.at(-1)?.[0] as {
      showSearch: boolean;
    };

    expect(grid_props.showSearch).toBe(true);
  });

  it("starts row markers from the page offset", () => {
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={rows}
        totalRowCount={200}
        page={2}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );

    const grid_props = data_editor_mock.mock.calls[0][0] as {
      rowMarkers: { kind: string; startIndex: number };
    };

    expect(grid_props.rowMarkers.startIndex).toBe(101);
  });

  it("formats null cells as read-only NULL values", () => {
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={[["Alice", null]]}
        totalRowCount={1}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );

    const grid_props = data_editor_mock.mock.calls[0][0] as {
      getCellContent: (cell: readonly [number, number]) => { displayData: string; readonly: boolean; style?: string };
    };

    expect(grid_props.getCellContent([1, 0])).toMatchObject({
      displayData: "NULL",
      readonly: true,
      style: "faded",
    });
  });

  it("calls onPageChange when Next is clicked", () => {
    const onPage = vi.fn();
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={rows}
        totalRowCount={200}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={onPage}
      />,
    );

    fireEvent.click(screen.getByText("Next"));
    expect(onPage).toHaveBeenCalledWith(2);
  });

  it("disables Previous on the first page and Next on the last page", () => {
    render(
      <DatasetPreviewGrid
        columns={columns}
        rows={rows}
        totalRowCount={5}
        page={1}
        pageSize={100}
        loading={false}
        error={null}
        onPageChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Previous")).toBeDisabled();
    expect(screen.getByText("Next")).toBeDisabled();
  });
});
