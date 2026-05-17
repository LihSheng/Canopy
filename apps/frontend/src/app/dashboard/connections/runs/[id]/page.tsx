import { Suspense } from "react";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import RunDetailContent from "./run-detail-content";

export default async function RunDetailPage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader title="Run Detail" />
      <AnalyticsBreadcrumb
        items={buildConnectionsBreadcrumbs(
          { label: "Run History", href: "/dashboard/connections/runs" },
          { label: "Run Detail" },
        )}
      />
      <div className="flex-1 overflow-auto p-6">
        <Suspense fallback={<LoadingSpinner text="Loading run..." />}>
          <RunDetailContent runId={id} />
        </Suspense>
      </div>
    </div>
  );
}
