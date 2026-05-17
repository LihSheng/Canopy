import { Suspense } from "react";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import DatasetWorkspaceContent from "./dataset-workspace-content";

export default async function DatasetWorkspacePage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader title="Dataset Workspace" />
      <AnalyticsBreadcrumb
        items={buildConnectionsBreadcrumbs(
          { label: "Datasets", href: "/dashboard/connections/datasets" },
          { label: "Dataset Workspace" },
        )}
      />
      <div className="flex-1 overflow-auto p-6">
        <Suspense fallback={<LoadingSpinner text="Loading dataset..." />}>
          <DatasetWorkspaceContent datasetId={id} />
        </Suspense>
      </div>
    </div>
  );
}
