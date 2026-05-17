import { Suspense } from "react";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import ConnectionsHomeContent from "./connections-home-content";

export default function ConnectionsPage() {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader title="Data Connections" />
      <AnalyticsBreadcrumb items={buildConnectionsBreadcrumbs({ label: "Data Connections" })} />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading connections..." />}>
          <ConnectionsHomeContent />
        </Suspense>
      </div>
    </div>
  );
}
