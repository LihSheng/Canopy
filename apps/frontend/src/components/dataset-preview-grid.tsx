"use client";

import { useEffect, useState } from "react";
import { DataEditor, GridCellKind, type GridCell, type GridColumn } from "@glideapps/glide-data-grid";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

type Props = {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  totalRowCount: number;
  page: number;
  pageSize: number;
  loading: boolean;
  error: string | null;
  onPageChange: (page: number) => void;
  onRetry?: () => void;
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

export function DatasetPreviewGrid({
  columns = [],
  rows = [],
  totalRowCount = 0,
  page,
  pageSize,
  loading,
  error,
  onPageChange,
  onRetry,
}: Props) {
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

  if (loading) {
    return <LoadingSpinner text="Loading preview data..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={onRetry} />;
  }

  if (!columns || columns.length === 0) {
    return <EmptyState title="No data available" description="This dataset has no columns to display." />;
  }

  const totalPages = Math.max(1, Math.ceil(totalRowCount / pageSize));
  const showingFrom = rows.length === 0 ? 0 : (page - 1) * pageSize + 1;
  const showingTo = (page - 1) * pageSize + rows.length;
  const grid_columns = buildGridColumns(columns);

  return (
    <div>
      {rows.length === 0 ? (
        <EmptyState title="No rows" description="This dataset contains no data." />
      ) : (
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
            className="h-[32rem] w-full"
            columns={grid_columns}
            rows={rows.length}
            rowMarkers={{ kind: "number", startIndex: (page - 1) * pageSize + 1 }}
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
        </div>
      )}

      <div className="mt-3 flex items-center justify-between text-xs text-zinc-500">
        <span>
          {rows.length > 0
            ? `Showing ${showingFrom}–${showingTo} of ${totalRowCount} rows`
            : "No rows"}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-md px-2.5 py-1 text-xs font-medium text-zinc-900 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-md px-2.5 py-1 text-xs font-medium text-zinc-900 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
