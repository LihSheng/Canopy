"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ReportPresetGrid } from "./report-preset-grid";
import { ReportHistoryList } from "./report-history-list";
import {
  fetchExportHistory,
  triggerExport,
  rerunExportJob,
  fetchExportJob,
} from "@/lib/api/reports";
import { mapReportsWorkspace } from "./report-mappers";
import { readDashboardState } from "@/lib/navigation/route-state";
import { TIME_RANGE_LABELS } from "@/lib/navigation/time-range";
import type { ReportsWorkspaceView, ExportPreset } from "./report-mappers";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; view: ReportsWorkspaceView };

export function ReportsPage() {
  const searchParams = useSearchParams();
  const { timeRange } = readDashboardState(searchParams);

  const [data, setData] = useState<DataState>({ status: "loading" });
  const [exporting, setExporting] = useState<ExportPreset["key"] | null>(null);
  const [rerunning, setRerunning] = useState<string | null>(null);

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const history = await fetchExportHistory();
      const view = mapReportsWorkspace(history.jobs);
      setData({ status: "success", view });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load reports",
      });
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleTrigger = useCallback(
    async (key: ExportPreset["key"]) => {
      setExporting(key);
      try {
        const job = await triggerExport(key, timeRange);
        await waitForJobCompletion(job.job_id);
      } catch {
        setExporting(null);
      }
    },
    [timeRange],
  );

  const handleRerun = useCallback(
    async (jobId: string) => {
      setRerunning(jobId);
      try {
        const job = await rerunExportJob(jobId);
        await waitForJobCompletion(job.job_id);
      } catch {
        setRerunning(null);
      }
    },
    [],
  );

  const waitForJobCompletion = useCallback(async (jobId: string) => {
    let attempts = 0;
    while (attempts < 60) {
      await new Promise((r) => setTimeout(r, 2000));
      const latest = await fetchExportJob(jobId);
      if (latest.status === "completed" || latest.status === "failed") {
        break;
      }
      attempts++;
    }
    setExporting(null);
    setRerunning(null);
    await load();
  }, [load]);

  const contextLabel = TIME_RANGE_LABELS[timeRange];

  if (data.status === "error") {
    return (
      <AnalyticsPageShell title="Reports" contextText={contextLabel}>
        <ErrorState message={data.message} onRetry={load} />
      </AnalyticsPageShell>
    );
  }

  const loading = data.status === "loading";

  return (
    <AnalyticsPageShell
      title="Reports"
      contextText={loading ? undefined : contextLabel}
    >
      {loading ? (
        <LoadingSpinner text="Loading reports..." />
      ) : data.status === "success" ? (
        <>
          <ReportPresetGrid
            presets={data.view.presets}
            onTrigger={handleTrigger}
            exporting={exporting}
          />
          <ReportHistoryList
            items={data.view.recentExports}
            onRerun={handleRerun}
            exporting={rerunning}
          />
        </>
      ) : null}
    </AnalyticsPageShell>
  );
}
