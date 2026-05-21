"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchDatasets } from "@/lib/api/data-source";
import type { Dataset } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";
import { CompactTable } from "@/components/shared/table";
import type { ColumnDef } from "@/components/shared/table";

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

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

  if (loading) return <LoadingSpinner text="Loading datasets..." />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  if (datasets.length === 0) {
    return (
      <CompactTable
        columns={DATASET_LIST_COLUMNS}
        rows={[]}
        getRowId={(row) => String(row.id)}
        emptyText="No datasets yet"
      />
    );
  }

  return (
    <CompactTable
      columns={DATASET_LIST_COLUMNS}
      rows={datasets as unknown as Record<string, unknown>[]}
      getRowId={(row) => String(row.id)}
      loading={loading}
      error={error}
      onRetry={retry}
      emptyText="No datasets yet"
    />
  );
}
export default DatasetListContent;
