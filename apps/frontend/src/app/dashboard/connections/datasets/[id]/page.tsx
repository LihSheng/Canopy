import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import DatasetWorkspaceContent from "./dataset-workspace-content";

export default async function DatasetWorkspacePage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <AnalyticsPageShell
      title="Dataset Workspace"
      breadcrumbItems={buildConnectionsBreadcrumbs(
        { label: "Datasets", href: "/dashboard/connections/datasets" },
        { label: "Dataset Workspace" },
      )}
    >
      <Suspense fallback={<LoadingSpinner text="Loading dataset..." />}>
        <DatasetWorkspaceContent datasetId={id} />
      </Suspense>
    </AnalyticsPageShell>
  );
}
