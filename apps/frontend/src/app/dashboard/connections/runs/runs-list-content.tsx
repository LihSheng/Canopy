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

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRuns();
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : errorMessageFailedToLoad("runs"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingSpinner text={UI_LABELS.loading} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

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
