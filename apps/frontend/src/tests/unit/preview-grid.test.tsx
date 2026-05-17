import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const data_editor_mock = vi.fn((_props: Record<string, unknown>) => {
  return <div data-testid="glide-grid" />;
});

vi.mock("@glideapps/glide-data-grid", () => ({
  DataEditor: (props: Record<string, unknown>) => data_editor_mock(props),
  GridCellKind: {
    Text: "text",
  },
}));

import { PreviewGrid } from "@/components/preview-grid";

beforeEach(() => {
  data_editor_mock.mockClear();
});

describe("PreviewGrid", () => {
  it("renders the glide grid for uploaded file previews", () => {
    render(
      <PreviewGrid
        columns={["name", "amount"]}
        rows={[
          ["Alice", 100],
          ["Bob", 200],
        ]}
        totalRowCount={2}
      />,
    );

    expect(screen.getByTestId("glide-grid")).toBeInTheDocument();
    const grid_props = data_editor_mock.mock.calls[0][0] as {
      columns: Array<{ title: string }>;
      rows: number;
      rowMarkers: { kind: string; startIndex: number };
      getCellContent: (cell: readonly [number, number]) => { displayData: string; readonly: boolean };
    };

    expect(grid_props.columns.map((column) => column.title)).toEqual(["name", "amount"]);
    expect(grid_props.rows).toBe(2);
    expect(grid_props.rowMarkers).toEqual({ kind: "number", startIndex: 1 });
    expect(grid_props.getCellContent([0, 0]).displayData).toBe("Alice");
    expect(grid_props.getCellContent([1, 0]).displayData).toBe("100");
  });

  it("starts with search hidden and provides close handler", () => {
    render(
      <PreviewGrid
        columns={["name", "amount"]}
        rows={[["Alice", 100]]}
        totalRowCount={1}
      />,
    );

    const grid_props = data_editor_mock.mock.calls[0][0] as {
      showSearch: boolean;
      onSearchClose: (() => void) | undefined;
      keybindings: { search: boolean };
    };

    expect(grid_props.showSearch).toBe(false);
    expect(grid_props.onSearchClose).toBeDefined();
    expect(grid_props.keybindings).toEqual({ search: true });
    expect(screen.getByRole("button", { name: "Search" })).toBeInTheDocument();
  });

  it("opens the search box from ctrl+f", () => {
    render(
      <PreviewGrid
        columns={["name", "amount"]}
        rows={[["Alice", 100]]}
        totalRowCount={1}
      />,
    );

    fireEvent.keyDown(window, { key: "f", ctrlKey: true });

    const grid_props = data_editor_mock.mock.calls.at(-1)?.[0] as {
      showSearch: boolean;
    };

    expect(grid_props.showSearch).toBe(true);
  });

  it("formats null cells as read-only NULL values", () => {
    render(
      <PreviewGrid
        columns={["name", "amount"]}
        rows={[["Alice", null]]}
        totalRowCount={1}
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

  it("shows the empty state when there are no columns", () => {
    render(<PreviewGrid columns={[]} rows={[]} totalRowCount={0} />);

    expect(screen.getByText("No data to display")).toBeInTheDocument();
  });
});
