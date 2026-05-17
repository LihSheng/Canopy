"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchDatasets, fetchRuns } from "@/lib/api/data-source";
import type { Dataset, Run } from "@/lib/api/types";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function ConnectionsHomeContent() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ds, rs] = await Promise.all([
        fetchDatasets().catch(() => []),
        fetchRuns().catch(() => []),
      ]);
      setDatasets(ds);
      setRuns(rs);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingSpinner text="Loading..." />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-zinc-900">Data Connection Workspace</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Manage sources, connections, datasets, and runs
          </p>
        </div>
        <Link
          href="/dashboard/connections/sources"
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
        >
          New Source
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <CardLink href="/dashboard/connections/sources" title="Source Catalog" description="Browse and connect to data sources" icon={
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" /></svg>
        } />
        <CardLink href="/dashboard/connections/datasets" title="Datasets" description={`${datasets.length} dataset${datasets.length !== 1 ? "s" : ""}`} icon={
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5"><path d="M12.232 4.232a3 3 0 014.242 4.242L6.828 18.07a2 2 0 01-1.414.586H3.5a.5.5 0 01-.5-.5v-1.914a2 2 0 01.586-1.414l8.646-8.646z" /><path d="M9.172 5.172a1 1 0 011.414 0l.707.707-5.657 5.657-.707-.707a1 1 0 010-1.414l4.243-4.243z" /></svg>
        } />
        <CardLink href="/dashboard/connections/runs" title="Run History" description={`${runs.length} recent run${runs.length !== 1 ? "s" : ""}`} icon={
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" /></svg>
        } />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-zinc-200 bg-white">
          <div className="border-b border-zinc-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-zinc-900">Recent Datasets</h3>
          </div>
          <div className="p-4">
            {datasets.length === 0 ? (
              <EmptyState title="No datasets" description="Create your first dataset from a source." />
            ) : (
              <ul className="space-y-2">
                {datasets.slice(0, 5).map((ds) => (
                  <li key={ds.id}>
                    <Link
                      href={`/dashboard/connections/datasets/${ds.id}`}
                      className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-zinc-700 transition-colors hover:bg-zinc-50"
                    >
                      <span className="font-medium">{ds.name}</span>
                      <span className="text-xs text-zinc-400">{ds.status}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-zinc-200 bg-white">
          <div className="border-b border-zinc-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-zinc-900">Recent Runs</h3>
          </div>
          <div className="p-4">
            {runs.length === 0 ? (
              <EmptyState title="No runs" description="Run a dataset to see results here." />
            ) : (
              <ul className="space-y-2">
                {runs.slice(0, 5).map((run) => (
                  <li key={run.id}>
                    <Link
                      href={`/dashboard/connections/runs/${run.id}`}
                      className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-zinc-700 transition-colors hover:bg-zinc-50"
                    >
                      <span className="font-medium">Run {run.id.slice(0, 8)}</span>
                      <span className="text-xs text-zinc-400">{run.status}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function CardLink({
  href,
  title,
  description,
  icon,
}: {
  href: string;
  title: string;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm transition-all hover:border-zinc-300 hover:shadow-md"
    >
      <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-zinc-100 text-zinc-600">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-zinc-900">{title}</h3>
      <p className="mt-1 text-xs text-zinc-500">{description}</p>
    </Link>
  );
}
