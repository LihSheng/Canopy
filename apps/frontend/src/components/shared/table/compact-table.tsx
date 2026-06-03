"use client";

import type { ChangeEvent } from "react";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { buttonToneStyles, sharedButtonBase } from "@/components/shared/ui-styles";
import type { ColumnDef, RowIdentity, TablePage, TableSelection } from "./types";

type CompactTableProps = {
  columns: ColumnDef[];
  rows: Record<string, unknown>[];
  getRowId: (row: Record<string, unknown>, index: number) => RowIdentity;
  loading?: boolean;
  error?: string | null;
  emptyText?: string;
  errorText?: string;
  onRetry?: () => void;
  page?: TablePage | null;
  onPageChange?: (page: number) => void;
  searchValue?: string;
  onSearchChange?: (value: string) => void;
  searchPlaceholder?: string;
  totalRowCount?: number;
  selection?: TableSelection | null;
};

const alignClass = (align?: "left" | "center" | "right"): string => {
  if (align === "right") return "text-right";
  if (align === "center") return "text-center";
  return "text-left";
};

const selectAllId = "compact-table-select-all";

export const CompactTable = ({
  columns,
  rows,
  getRowId,
  loading = false,
  error = null,
  emptyText,
  errorText,
  onRetry,
  page = null,
  onPageChange,
  searchValue,
  onSearchChange,
  searchPlaceholder = "Search...",
  selection = null,
}: CompactTableProps) => {
  if (loading) {
    return <LoadingSpinner text="Loading..." />;
  }

  if (error) {
    return <ErrorState message={errorText ?? error} onRetry={onRetry} />;
  }

  if (rows.length === 0) {
    return (
      <div>
        {onSearchChange && searchValue !== undefined && (
          <div className="mb-3">
            <input
              type="text"
              value={searchValue}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full max-w-xs rounded-lg border border-zinc-200 px-3 py-2 text-sm placeholder:text-zinc-400 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}
        <EmptyState title={emptyText ?? "No data available"} />
      </div>
    );
  }

  const hasSelection = selection !== null;

  return (
    <div>
      {onSearchChange && searchValue !== undefined && (
        <div className="mb-3">
          <input
            type="text"
            value={searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full max-w-xs border border-zinc-200 rounded-lg px-3 py-2 text-sm placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      )}

      <div className="max-h-[min(32rem,calc(100dvh-22rem))] overflow-auto rounded-lg border border-zinc-200">
        <table className="min-w-full divide-y divide-zinc-200 text-sm">
          <thead>
            <tr className="bg-zinc-50">
              {hasSelection && (
                <th className="w-10 whitespace-nowrap px-3 py-3">
                  <input
                    id={selectAllId}
                    type="checkbox"
                    checked={selection.allSelected}
                    ref={(el) => {
                      if (el) {
                        el.indeterminate = !selection.allSelected && selection.someSelected;
                      }
                    }}
                    onChange={selection.onToggleAll}
                    className="h-4 w-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                  />
                </th>
              )}
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`whitespace-nowrap px-4 py-3 ${alignClass(col.align)} text-xs font-semibold uppercase tracking-wider text-zinc-500`}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {rows.map((row, rowIndex) => {
              const rowId = getRowId(row, rowIndex);
              const isSelected = hasSelection && selection.selectedIds.has(String(rowId));
              return (
                <tr key={rowId} className="hover:bg-zinc-50">
                  {hasSelection && (
                    <td className="whitespace-nowrap px-3 py-3">
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => selection.onToggleRow(String(rowId))}
                        className="h-4 w-4 rounded border-zinc-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                      />
                    </td>
                  )}
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={`whitespace-nowrap px-4 py-3 ${alignClass(col.align)} text-zinc-700`}
                    >
                      {col.render
                        ? col.render(row[col.key], row, rowIndex)
                        : String(row[col.key] ?? "")}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {page && onPageChange && (
        <div className="mt-3 flex items-center justify-between">
          <button
            onClick={() => onPageChange(page.current - 1)}
            disabled={page.current <= 1}
            className={`${sharedButtonBase} ${buttonToneStyles.secondary} px-3 py-1.5`}
          >
            Previous
          </button>
          <span className="text-sm text-zinc-600">
            Page {page.current} of {page.total}
          </span>
          <button
            onClick={() => onPageChange(page.current + 1)}
            disabled={page.current >= page.total}
            className={`${sharedButtonBase} ${buttonToneStyles.secondary} px-3 py-1.5`}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
