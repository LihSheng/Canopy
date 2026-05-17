import { Suspense } from "react";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import RunDetailContent from "./run-detail-content";

export default async function RunDetailPage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader title="Run Detail" />
      <div className="flex-1 overflow-auto p-6">
        <Suspense fallback={<LoadingSpinner text="Loading run..." />}>
          <RunDetailContent runId={id} />
        </Suspense>
      </div>
    </div>
  );
}
