"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  getHealthSummary,
  getHealthTrends,
  getPipelineCatalog,
  getPipelineDetail,
  getRunDetail,
  refreshHealthRollups,
  backfillHealthRollups,
  type HealthSummary,
  type DailyTrend,
  type PipelineSummary,
  type PipelineDetail,
  type RunDetail,
} from "@/lib/api/admin-health";
import { ROUTES } from "@/lib/constants";
import { KpiCard } from "./kpi-card";
import { TrendChart } from "./trend-chart";
import { PipelineTable } from "./pipeline-table";
import { PipelineDetailView } from "./pipeline-detail-view";
import { RunDetailDrawer } from "./run-detail-drawer";

type ViewState =
  | { page: "summary" }
  | { page: "pipeline-detail"; pipelineId: string }
  | { page: "run-detail"; runId: string };

export const DataHealthPageContent = () => {
  const [summary, setSummary] = useState<HealthSummary | null>(null);
  const [trends, setTrends] = useState<DailyTrend[]>([]);
  const [pipelines, setPipelines] = useState<PipelineSummary[]>([]);
  const [pipelineDetail, setPipelineDetail] = useState<PipelineDetail | null>(null);
  const [runDetail, setRunDetail] = useState<RunDetail | null>(null);
  const [view, setView] = useState<ViewState>({ page: "summary" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [healthFilter, setHealthFilter] = useState<string | undefined>();
  const [pipelineDetailLoading, setPipelineDetailLoading] = useState(false);
  const [runDetailLoading, setRunDetailLoading] = useState(false);
  const [rollupActionLoading, setRollupActionLoading] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [summaryData, trendsData, pipelinesData] = await Promise.all([
        getHealthSummary(),
        getHealthTrends(30),
        getPipelineCatalog(healthFilter),
      ]);
      setError(null);
      setSummary(summaryData);
      setTrends(trendsData);
      setPipelines(pipelinesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load health data");
    } finally {
      setLoading(false);
    }
  }, [healthFilter]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

  const handlePipelineClick = async (pipelineId: string) => {
    setView({ page: "pipeline-detail", pipelineId });
    setPipelineDetailLoading(true);
    setPipelineDetail(null);
    try {
      const detail = await getPipelineDetail(pipelineId);
      setPipelineDetail(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load pipeline detail");
    } finally {
      setPipelineDetailLoading(false);
    }
  };

  const handleRunClick = async (runId: string) => {
    setView({ page: "run-detail", runId });
    setRunDetailLoading(true);
    setRunDetail(null);
    try {
      const detail = await getRunDetail(runId);
      setRunDetail(detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load run detail");
    } finally {
      setRunDetailLoading(false);
    }
  };

  const handleBackToSummary = () => {
    setView({ page: "summary" });
    setPipelineDetail(null);
    setRunDetail(null);
  };

  const handleRefreshRollups = async () => {
    setRollupActionLoading(true);
    setError(null);
    try {
      await refreshHealthRollups();
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh rollups");
    } finally {
      setRollupActionLoading(false);
    }
  };

  const handleBackfillRollups = async () => {
    setRollupActionLoading(true);
    setError(null);
    try {
      await backfillHealthRollups(30);
      await fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to backfill rollups");
    } finally {
      setRollupActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <p className="text-sm text-zinc-500">Loading data health...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
          <p className="text-sm text-red-800">{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 rounded-md bg-red-100 px-4 py-2 text-sm font-medium text-red-800 hover:bg-red-200"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (view.page === "run-detail") {
    return (
      <div className="space-y-6 p-6">
        <button
          onClick={handleBackToSummary}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          &larr; Back to Data Health
        </button>
        <RunDetailDrawer
          runDetail={runDetail}
          loading={runDetailLoading}
          onPipelineClick={handlePipelineClick}
        />
      </div>
    );
  }

  if (view.page === "pipeline-detail") {
    return (
      <div className="space-y-6 p-6">
        <button
          onClick={handleBackToSummary}
          className="text-sm font-medium text-indigo-600 hover:text-indigo-800"
        >
          &larr; Back to Data Health
        </button>
        <PipelineDetailView
          detail={pipelineDetail}
          loading={pipelineDetailLoading}
          onRunClick={handleRunClick}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
          Data Health
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Operational health overview for the last 30 days
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            onClick={handleRefreshRollups}
            disabled={rollupActionLoading}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
          >
            Refresh Rollups
          </button>
          <button
            onClick={handleBackfillRollups}
            disabled={rollupActionLoading}
            className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
          >
            Backfill 30d
          </button>
        </div>
      </div>

      {summary && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <KpiCard
            label="Bytes Written (30d)"
            value={formatBytes(summary.bytes_written_30d)}
            trend={trends.length > 1 ? getTrendDirection(trends, "bytes_written") : undefined}
          />
          <KpiCard
            label="Errors (30d)"
            value={summary.error_count_30d.toString()}
            trend={trends.length > 1 ? getTrendDirection(trends, "errors") : undefined}
            variant={summary.error_count_30d > 0 ? "danger" : "normal"}
          />
          <KpiCard
            label="Warnings (30d)"
            value={summary.warning_count_30d.toString()}
            variant={summary.warning_count_30d > 0 ? "warning" : "normal"}
          />
          <KpiCard
            label="SLA Violations (30d)"
            value={summary.sla_violation_count_30d.toString()}
            variant={summary.sla_violation_count_30d > 0 ? "warning" : "normal"}
          />
          <KpiCard
            label="Total Runs (30d)"
            value={summary.total_runs_30d.toString()}
          />
          <KpiCard
            label="Active Pipelines"
            value={summary.active_pipeline_count.toString()}
          />
        </div>
      )}

      {/* System Status */}
      {summary && (
        <SystemStatusBadge pipelines={pipelines} />
      )}

      {/* Trends Chart */}
      {trends.length > 0 && (
        <TrendChart data={trends} />
      )}

      {/* Pipeline Table */}
      <PipelineTable
        pipelines={pipelines}
        healthFilter={healthFilter}
        onHealthFilterChange={setHealthFilter}
        onPipelineClick={handlePipelineClick}
      />

      {/* Recent Failures */}
      {summary && summary.recent_failures.length > 0 && (
        <RecentFailuresTable
          failures={summary.recent_failures}
          onRunClick={handleRunClick}
        />
      )}
    </div>
  );
};

const SystemStatusBadge = ({ pipelines }: { pipelines: PipelineSummary[] }) => {
  const hasFailed = pipelines.some((p) => p.health === "failed");
  const hasDegraded = pipelines.some((p) => p.health === "degraded");

  let status: string;
  let className: string;
  if (hasFailed) {
    status = "System Status: FAILED";
    className = "bg-red-100 text-red-800";
  } else if (hasDegraded) {
    status = "System Status: WARNING";
    className = "bg-amber-100 text-amber-800";
  } else {
    status = "System Status: HEALTHY";
    className = "bg-green-100 text-green-800";
  }

  return (
    <div className="inline-block rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <span className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${className}`}>
        {status}
      </span>
    </div>
  );
};

const RecentFailuresTable = ({
  failures,
  onRunClick,
}: {
  failures: { id: string; run_id: string; pipeline_id: string; dataset_id: string | null; connection_id: string | null; error_message: string; finished_at: string | null }[];
  onRunClick: (runId: string) => void;
}) => {
  return (
    <div className="rounded-lg border border-zinc-200 bg-white">
      <div className="border-b border-zinc-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-zinc-900">Recent Failed Runs</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-zinc-200">
          <thead className="bg-zinc-50">
            <tr>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Pipeline
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Error
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Finished At
              </th>
              <th className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-zinc-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-200">
            {failures.map((f) => (
              <tr key={f.id} className="hover:bg-zinc-50">
                <td className="whitespace-nowrap px-4 py-2 text-sm font-medium text-zinc-900">
                  {f.pipeline_id}
                </td>
                <td className="max-w-md truncate px-4 py-2 text-sm text-red-700">
                  {f.error_message || "No error message"}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-sm text-zinc-500">
                  {f.finished_at ? new Date(f.finished_at).toLocaleString() : "-"}
                </td>
                <td className="whitespace-nowrap px-4 py-2 text-sm">
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => onRunClick(f.run_id)}
                      className="font-medium text-indigo-600 hover:text-indigo-800 text-left"
                    >
                      View Run
                    </button>
                    {f.dataset_id && (
                      <Link
                        href={ROUTES.connections.datasetLineage(f.dataset_id)}
                        className="font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        View Dataset Lineage
                      </Link>
                    )}
                    {f.connection_id && (
                      <Link
                        href={ROUTES.connections.connectionLineage(f.connection_id)}
                        className="font-medium text-indigo-600 hover:text-indigo-800"
                      >
                        View Connection Lineage
                      </Link>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  const value = bytes / Math.pow(1024, i);
  return `${value.toFixed(1)} ${units[i]}`;
}

function getTrendDirection(
  trends: DailyTrend[],
  field: "bytes_written" | "errors"
): "up" | "down" | "stable" {
  if (trends.length < 7) return "stable";
  const recent = trends.slice(-7);
  const first = recent[0][field];
  const last = recent[recent.length - 1][field];
  if (last > first * 1.1) return "up";
  if (last < first * 0.9) return "down";
  return "stable";
}
