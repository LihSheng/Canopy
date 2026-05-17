"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchDatasets } from "@/lib/api/v4";
import type { Dataset } from "@/lib/api/types";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

const statusColor: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  draft: "bg-zinc-100 text-zinc-600",
  error: "bg-red-100 text-red-800",
  processing: "bg-blue-100 text-blue-800",
};

export default function DatasetListContent() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDatasets();
      setDatasets(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingSpinner text="Loading datasets..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  if (datasets.length === 0) {
    return (
      <EmptyState
        title="No datasets yet"
        description="Upload a file from the source catalog to create your first dataset."
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-zinc-200">
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead>
          <tr className="bg-zinc-50">
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Source Object
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Created
            </th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {datasets.map((ds) => (
            <tr key={ds.id} className="hover:bg-zinc-50">
              <td className="px-4 py-3">
                <Link
                  href={`/dashboard/connections/datasets/${ds.id}`}
                  className="font-medium text-indigo-600 hover:text-indigo-500"
                >
                  {ds.name}
                </Link>
              </td>
              <td className="px-4 py-3 text-zinc-700">{ds.source_object_name}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                    statusColor[ds.status] || "bg-zinc-100 text-zinc-600"
                  }`}
                >
                  {ds.status}
                </span>
              </td>
              <td className="px-4 py-3 text-zinc-500">
                {new Date(ds.created_at).toLocaleDateString()}
              </td>
              <td className="px-4 py-3 text-right">
                <Link
                  href={`/dashboard/connections/datasets/${ds.id}`}
                  className="text-xs font-medium text-indigo-600 hover:text-indigo-500"
                >
                  Open
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
