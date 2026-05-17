import { Suspense } from "react";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import RunsListContent from "./runs-list-content";

export default function RunsPage() {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsBreadcrumb items={buildConnectionsBreadcrumbs({ label: "Run History" })} />
      <AnalyticsHeader
        title="Run History"
        contextText="All dataset processing runs"
      />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading runs..." />}>
          <RunsListContent />
        </Suspense>
      </div>
    </div>
  );
}
