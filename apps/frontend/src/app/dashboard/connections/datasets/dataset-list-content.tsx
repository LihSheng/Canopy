"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  fetchDatasets,
  fetchBulkDeleteSummary,
  bulkDeleteDatasets,
} from "@/lib/api/data-source";
import type {
  Dataset,
  DatasetBulkDeleteSummaryItem,
  DatasetBulkDeleteResult,
} from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";
import { CompactTable } from "@/components/shared/table";
import type { ColumnDef, TableSelection } from "@/components/shared/table";
import { buttonToneStyles, sharedButtonBase } from "@/components/shared/ui-styles";
import { useToast } from "@/components/shared/toast";

const statusColor: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  draft: "bg-zinc-100 text-zinc-600",
  error: "bg-red-100 text-red-800",
  processing: "bg-blue-100 text-blue-800",
};

const DATASET_LIST_COLUMNS: ColumnDef[] = [
  {
    key: "name",
    header: "Name",
    render: (value, row) => (
      <Link
        href={`/dashboard/connections/datasets/${row.id}`}
        className="font-medium text-indigo-600 hover:text-indigo-500"
      >
        {String(value ?? "")}
      </Link>
    ),
  },
  { key: "source_object_name", header: "Source Object" },
  {
    key: "status",
    header: "Status",
    render: (value) => (
      <span
        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
          statusColor[String(value ?? "")] || "bg-zinc-100 text-zinc-600"
        }`}
      >
        {String(value ?? "")}
      </span>
    ),
  },
  {
    key: "created_at",
    header: "Created",
    render: (value) =>
      new Date(String(value ?? "")).toLocaleDateString(),
  },
  {
    key: "actions",
    header: "",
    align: "right",
    render: (value, row) => (
      <Link
        href={`/dashboard/connections/datasets/${row.id}`}
        className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
      >
        Open
      </Link>
    ),
  },
];

const DatasetListContent = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [searchValue, setSearchValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Bulk delete dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteSummary, setDeleteSummary] = useState<DatasetBulkDeleteSummaryItem[] | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteResult, setDeleteResult] = useState<DatasetBulkDeleteResult | null>(null);

  const toast = useToast();

  const filteredDatasets = useMemo(() => {
    const query = searchValue.trim().toLowerCase();
    if (!query) {
      return datasets;
    }

    return datasets.filter((dataset) => {
      const searchableText = [
        dataset.name,
        dataset.source_object_name,
        dataset.status,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return searchableText.includes(query);
    });
  }, [datasets, searchValue]);

  const filteredIds = useMemo(() => {
    return new Set(filteredDatasets.map((d) => d.id));
  }, [filteredDatasets]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchDatasets();
        if (!cancelled) setDatasets(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load datasets");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [retryKey]);

  const retry = useCallback(() => setRetryKey((k) => k + 1), []);

  const toggleRow = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    setSelectedIds((prev) => {
      // If all current-page rows are selected, deselect them.
      // Otherwise, select all current-page rows.
      const allSelected = filteredDatasets.every((d) => prev.has(d.id));
      if (allSelected) {
        const next = new Set(prev);
        filteredDatasets.forEach((d) => next.delete(d.id));
        return next;
      }
      const next = new Set(prev);
      filteredDatasets.forEach((d) => next.add(d.id));
      return next;
    });
  }, [filteredDatasets]);

  const allSelected = filteredDatasets.length > 0 && filteredDatasets.every((d) => selectedIds.has(d.id));
  const someSelected = filteredDatasets.some((d) => selectedIds.has(d.id));

  const selection: TableSelection = {
    selectedIds,
    onToggleRow: toggleRow,
    onToggleAll: toggleAll,
    allSelected,
    someSelected,
  };

  const selectedCount = selectedIds.size;

  // Clear selection when datasets change (e.g. after refresh or delete)
  useEffect(() => {
    setSelectedIds((prev) => {
      const kept = new Set<string>();
      for (const id of prev) {
        if (filteredIds.has(id) || datasets.some((d) => d.id === id)) {
          kept.add(id);
        }
      }
      return kept;
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [datasets]);

  const handleOpenDeleteConfirm = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    try {
      const summary = await fetchBulkDeleteSummary(ids);
      setDeleteSummary(summary);
      setDeleteResult(null);
      setDeleteDialogOpen(true);
    } catch (err) {
      toast.danger("Failed to check delete eligibility", err instanceof Error ? err.message : "Unknown error");
    }
  }, [selectedIds, toast]);

  const handleConfirmDelete = useCallback(async () => {
    const ids = Array.from(selectedIds);
    if (ids.length === 0) return;

    setDeleting(true);
    try {
      const result = await bulkDeleteDatasets(ids);
      setDeleteResult(result);
      setDeleteSummary(null);

      if (result.deleted.length > 0) {
        toast.success(
          "Datasets deleted",
          `${result.deleted.length} dataset(s) deleted.`,
        );
      }
      if (result.skipped.length > 0) {
        toast.warning(
          "Some datasets skipped",
          `${result.skipped.length} dataset(s) could not be deleted.`,
        );
      }
      if (result.deleted.length === 0 && result.skipped.length > 0) {
        toast.danger(
          "No datasets deleted",
          `All ${result.skipped.length} selected dataset(s) were blocked.`,
        );
      }

      // Refresh list and clear selection
      setSelectedIds(new Set());
      setRetryKey((k) => k + 1);
    } catch (err) {
      toast.danger("Bulk delete failed", err instanceof Error ? err.message : "Unknown error");
    } finally {
      setDeleting(false);
    }
  }, [selectedIds, toast]);

  const handleCloseDialog = useCallback(() => {
    if (!deleting) {
      setDeleteDialogOpen(false);
      setDeleteSummary(null);
      setDeleteResult(null);
    }
  }, [deleting]);

  const deletableRows = deleteSummary?.filter((s) => s.can_delete) ?? [];
  const skippedRows = deleteSummary?.filter((s) => !s.can_delete) ?? [];

  // ── Render ──

  if (loading) return <LoadingSpinner text="Loading datasets..." />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  return (
    <div>
      {/* Bulk action bar */}
      {selectedCount > 0 && (
        <div className="mb-3 flex items-center gap-3 rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-2.5">
          <span className="text-sm font-medium text-indigo-800">
            {selectedCount} selected
          </span>
          <div className="flex-1" />
          <button
            type="button"
            onClick={handleOpenDeleteConfirm}
            className={`${sharedButtonBase} ${buttonToneStyles.danger}`}
          >
            Delete selected
          </button>
        </div>
      )}

      {datasets.length === 0 ? (
        <CompactTable
          columns={DATASET_LIST_COLUMNS}
          rows={[]}
          getRowId={(row) => String(row.id)}
          searchValue={searchValue}
          onSearchChange={setSearchValue}
          searchPlaceholder="Search datasets..."
          emptyText="No datasets yet"
        />
      ) : (
        <CompactTable
          columns={DATASET_LIST_COLUMNS}
          rows={filteredDatasets as unknown as Record<string, unknown>[]}
          getRowId={(row) => String(row.id)}
          loading={loading}
          error={error}
          onRetry={retry}
          searchValue={searchValue}
          onSearchChange={setSearchValue}
          searchPlaceholder="Search datasets..."
          emptyText={searchValue.trim() ? "No datasets match your search" : "No datasets yet"}
          selection={selection}
        />
      )}

      {/* Bulk delete confirmation dialog */}
      {deleteDialogOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4 py-6"
          role="dialog"
          aria-modal="true"
          aria-labelledby="bulk-delete-dialog-title"
          onClick={(e) => {
            if (e.target === e.currentTarget && !deleting) {
              handleCloseDialog();
            }
          }}
        >
          <div className="absolute inset-0 bg-zinc-950/40 backdrop-blur-[1px]" aria-hidden />
          <div className="relative w-full max-w-lg rounded-2xl border border-zinc-200 bg-white p-6 shadow-2xl max-h-[80vh] overflow-y-auto">
            <h2 id="bulk-delete-dialog-title" className="text-lg font-semibold text-zinc-900">
              Delete selected datasets?
            </h2>

            {deleteResult ? (
              /* ── Result summary view ── */
              <div className="mt-4 space-y-3">
                {deleteResult.deleted.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-green-700">
                      Deleted ({deleteResult.deleted.length})
                    </p>
                    <ul className="mt-1 space-y-1">
                      {deleteResult.deleted.map((d) => (
                        <li key={d.dataset_id} className="text-sm text-zinc-600 pl-4 list-disc">
                          {d.dataset_name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {deleteResult.skipped.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-amber-700">
                      Skipped ({deleteResult.skipped.length})
                    </p>
                    <ul className="mt-1 space-y-1">
                      {deleteResult.skipped.map((s) => (
                        <li key={s.dataset_id} className="text-sm text-zinc-600 pl-4 list-disc">
                          {s.dataset_name ?? s.dataset_id}: {s.reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {deleteResult.deleted.length === 0 && deleteResult.skipped.length === 0 && (
                  <p className="text-sm text-zinc-500">No datasets were processed.</p>
                )}
                <div className="mt-6 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={handleCloseDialog}
                    className={`${sharedButtonBase} ${buttonToneStyles.secondary}`}
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : deleteSummary ? (
              /* ── Pre-confirm view ── */
              <div className="mt-4 space-y-3">
                {deletableRows.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-green-700">
                      Will be deleted ({deletableRows.length})
                    </p>
                    <ul className="mt-1 space-y-1">
                      {deletableRows.map((d) => (
                        <li key={d.dataset_id} className="text-sm text-zinc-600 pl-4 list-disc">
                          {d.dataset_name ?? d.dataset_id}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {skippedRows.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-amber-700">
                      Will be skipped ({skippedRows.length})
                    </p>
                    <ul className="mt-1 space-y-1">
                      {skippedRows.map((s) => (
                        <li key={s.dataset_id} className="text-sm text-zinc-600 pl-4 list-disc">
                          {s.dataset_name ?? s.dataset_id}: {s.blocking_reason ?? "Unknown reason"}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {deletableRows.length === 0 && skippedRows.length === 0 && (
                  <p className="text-sm text-zinc-500">No datasets to process.</p>
                )}
                <div className="mt-6 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={handleCloseDialog}
                    disabled={deleting}
                    className={`${sharedButtonBase} ${buttonToneStyles.secondary}`}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleConfirmDelete}
                    disabled={deleting || deletableRows.length === 0}
                    className={`${sharedButtonBase} ${buttonToneStyles.danger}`}
                  >
                    {deleting ? "Deleting..." : `Delete ${deletableRows.length} dataset(s)`}
                  </button>
                </div>
              </div>
            ) : (
              <div className="mt-4">
                <LoadingSpinner text="Checking datasets..." />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
export default DatasetListContent;
