import { Suspense } from "react";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import DatasetListContent from "./dataset-list-content";

export default function DatasetsPage() {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader
        title="Datasets"
        contextText="Browse and manage datasets"
      />
      <AnalyticsBreadcrumb items={buildConnectionsBreadcrumbs({ label: "Datasets" })} />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading datasets..." />}>
          <DatasetListContent />
        </Suspense>
      </div>
    </div>
  );
}
