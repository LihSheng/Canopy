import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import DatasetListContent from "./dataset-list-content";

export default function DatasetsPage() {
  return (
    <AnalyticsPageShell
      title="Datasets"
      contextText="Browse and manage datasets"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Datasets" })}
    >
      <Suspense fallback={<LoadingSpinner text="Loading datasets..." />}>
        <DatasetListContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
