"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  fetchDataset,
  fetchDatasetPreview,
  fetchDatasetVersions,
  fetchDatasetHealth,
  fetchDatasetLineage,
  fetchRuns,
} from "@/lib/api/data-source";
import type { Dataset, DatasetVersion, DatasetHealth, Run } from "@/lib/api/types";
import type { DatasetPreviewResponse } from "@/lib/api/data-source";
import { DatasetPreviewGrid } from "@/components/dataset-preview-grid";
import { DatasetSummaryCards } from "@/components/dataset-summary-cards";
import { DatasetCharts } from "@/components/dataset-charts";
import { VersionHistory } from "@/components/version-history";
import { HealthPanel } from "@/components/health-panel";
import { RunHistory } from "@/components/run-history";
import { LineageView } from "@/components/lineage-view";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

const TABS = ["Overview", "Preview", "Schema", "Transform", "Lineage", "Runs", "Details"] as const;

type Tab = (typeof TABS)[number];

type Props = {
  datasetId: string;
};

export default function DatasetWorkspaceContent({ datasetId }: Props) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeTab = (searchParams.get("tab") as Tab) || "Overview";

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [previewPage, setPreviewPage] = useState(1);
  const [previewPageSize] = useState(100);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [health, setHealth] = useState<DatasetHealth | null>(null);
  const [lineage, setLineage] = useState<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] } | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeVersion = versions.find((v) => v.id === dataset?.active_version_id);
  const activeVersionNumber = activeVersion?.version_number;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ds, versionsData, healthData, lineageData, runsData] =
        await Promise.all([
          fetchDataset(datasetId),
          fetchDatasetVersions(datasetId),
          fetchDatasetHealth(datasetId),
          fetchDatasetLineage(datasetId),
          fetchRuns(datasetId),
        ]);
      setDataset(ds);
      setVersions(versionsData);
      setHealth(healthData);
      setLineage(lineageData);
      setRuns(runsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dataset");
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const loadPreview = useCallback(async () => {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const previewData = await fetchDatasetPreview(datasetId, {
        page: previewPage,
        page_size: previewPageSize,
      });
      setPreview(previewData);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Failed to load preview");
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  }, [datasetId, previewPage, previewPageSize]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    loadPreview();
  }, [loadPreview]);

  const setTab = (tab: Tab) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  if (loading) return <LoadingSpinner text="Loading dataset workspace..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!dataset) return <ErrorState message="Dataset not found" />;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-zinc-900">{dataset.name}</h2>
        <p className="mt-1 text-sm text-zinc-500">
          {dataset.source_object_name} &middot; {dataset.status}
        </p>
      </div>

      <div className="border-b border-zinc-200">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setTab(tab)}
              className={`pb-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "border-b-2 border-zinc-900 text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      <div>
        {activeTab === "Overview" && (
          <div className="space-y-6">
            <DatasetSummaryCards
              health={health}
              versionCount={versions.length}
              activeVersionNumber={activeVersionNumber}
            />
            <DatasetCharts
              columns={preview?.columns ?? []}
              rows={preview?.rows ?? []}
              loading={previewLoading}
              error={previewError}
            />
            <VersionHistory
              versions={versions}
              activeVersionId={dataset.active_version_id}
            />
          </div>
        )}

        {activeTab === "Preview" && (
          <div className="space-y-3">
            <span className="inline-block rounded-full border border-zinc-300 bg-zinc-50 px-2.5 py-0.5 text-xs font-medium text-zinc-500">
              Read only
            </span>
            <DatasetPreviewGrid
              columns={preview?.columns ?? []}
              rows={preview?.rows ?? []}
              totalRowCount={preview?.total_row_count ?? 0}
              page={previewPage}
              pageSize={previewPageSize}
              loading={previewLoading}
              error={previewError}
              onPageChange={(page) => setPreviewPage(page)}
              onRetry={loadPreview}
            />
          </div>
        )}

        {activeTab === "Schema" && (
          <div className="rounded-lg border border-zinc-200">
            <table className="min-w-full divide-y divide-zinc-200 text-sm">
              <thead>
                <tr className="bg-zinc-50">
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Column Name
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {preview?.columns.map((col) => (
                  <tr key={col} className="hover:bg-zinc-50">
                    <td className="px-4 py-2 font-medium text-zinc-900">{col}</td>
                    <td className="px-4 py-2 text-zinc-500">text</td>
                  </tr>
                ))}
                {(!preview || preview.columns.length === 0) && (
                  <tr>
                    <td colSpan={2} className="px-4 py-8 text-center text-sm text-zinc-500">
                      No schema information available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "Transform" && (
          <div className="flex items-center justify-center py-16 text-sm text-zinc-500">
            Transform editor coming soon
          </div>
        )}

        {activeTab === "Lineage" && lineage && (
          <LineageView nodes={lineage.nodes} edges={lineage.edges} />
        )}

        {activeTab === "Runs" && (
          <RunHistory runs={runs} datasetId={datasetId} />
        )}

        {activeTab === "Details" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <h3 className="text-sm font-semibold text-zinc-900">Dataset Info</h3>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">ID</dt>
                    <dd className="text-zinc-900">{dataset.id}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Created</dt>
                    <dd className="text-zinc-900">
                      {new Date(dataset.created_at).toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Updated</dt>
                    <dd className="text-zinc-900">
                      {new Date(dataset.updated_at).toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Active Version</dt>
                    <dd className="text-zinc-900">
                      {dataset.active_version_id
                        ? versions.find((v) => v.id === dataset.active_version_id)
                            ?.version_number ?? dataset.active_version_id.slice(0, 8)
                        : "None"}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Versions</dt>
                    <dd className="text-zinc-900">{versions.length}</dd>
                  </div>
                </dl>
              </div>
            </div>
            <div className="lg:col-span-1">
              {health && <HealthPanel health={health} />}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
