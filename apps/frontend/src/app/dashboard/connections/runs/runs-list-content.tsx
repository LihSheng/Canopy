"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchRuns } from "@/lib/api/data-source";
import type { Run } from "@/lib/api/types";
import { RunHistory } from "@/components/run-history";
import { EmptyState } from "@/components/shared/empty-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";
import { UI_LABELS, errorMessageFailedToLoad } from "@/lib/constants";

const RunsListContent = () => {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchRuns();
        if (!cancelled) setRuns(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : errorMessageFailedToLoad("runs"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [retryKey]);

  const retry = useCallback(() => setRetryKey((k) => k + 1), []);

  if (loading) return <LoadingSpinner text={UI_LABELS.loading} />;
  if (error) return <ErrorState message={error} onRetry={retry} />;

  if (runs.length === 0) {
    return (
      <EmptyState
        title={UI_LABELS.noRunsYet}
        description="Run a dataset to see processing history here."
      />
    );
  }

  return <RunHistory runs={runs} />;
}
export default RunsListContent;
