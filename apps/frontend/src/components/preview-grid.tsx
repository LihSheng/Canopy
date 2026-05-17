"use client";

import { useEffect, useState } from "react";
import { DataEditor, GridCellKind, type GridCell, type GridColumn } from "@glideapps/glide-data-grid";

type Props = {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  totalRowCount: number;
};

function formatCellValue(value: string | number | boolean | null): GridCell {
  if (value === null) {
    return {
      kind: GridCellKind.Text,
      data: "",
      displayData: "NULL",
      allowOverlay: false,
      readonly: true,
      style: "faded",
    };
  }

  const display_value = String(value);

  return {
    kind: GridCellKind.Text,
    data: display_value,
    displayData: display_value,
    allowOverlay: false,
    readonly: true,
  };
}

function buildGridColumns(columns: string[]): GridColumn[] {
  return columns.map((column_name) => ({
    id: column_name,
    title: column_name,
    width: Math.max(160, Math.min(320, column_name.length * 12 + 48)),
  }));
}

export function PreviewGrid({ columns = [], rows = [], totalRowCount = 0 }: Props) {
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "f") {
        event.preventDefault();
        event.stopPropagation();
        setShowSearch(true);
      }
    }

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  if (!columns || columns.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No data to display
      </div>
    );
  }

  const grid_columns = buildGridColumns(columns);

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <div className="flex items-center justify-between border-b border-zinc-100 px-3 py-2 text-xs text-zinc-500">
        <span>Preview rows</span>
        <button
          type="button"
          onClick={() => setShowSearch(true)}
          className="rounded-md px-2.5 py-1 font-medium text-zinc-900 hover:bg-zinc-100"
        >
          Search
        </button>
      </div>
      <DataEditor
        className="h-[22rem] w-full"
        columns={grid_columns}
        rows={rows.length}
        rowMarkers={{ kind: "number", startIndex: 1 }}
        getCellContent={(cell) => {
          const [column_index, row_index] = cell;
          return formatCellValue(rows[row_index]?.[column_index] ?? null);
        }}
        showSearch={showSearch}
        onSearchClose={() => setShowSearch(false)}
        keybindings={{ search: true }}
        getCellsForSelection={true}
        onPaste={false}
        editOnType={false}
        freezeColumns={1}
      />
      <div className="border-t border-zinc-100 px-3 py-2 text-xs text-zinc-500">
        Showing {rows.length} of {totalRowCount} rows
      </div>
    </div>
  );
}
