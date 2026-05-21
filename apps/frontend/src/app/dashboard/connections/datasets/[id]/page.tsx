import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ROUTES, UI_LABELS } from "@/lib/constants";
import DatasetWorkspaceContent from "./dataset-workspace-content";

export default async function DatasetWorkspacePage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <AnalyticsPageShell
      title="Dataset Workspace"
      breadcrumbItems={buildConnectionsBreadcrumbs(
        { label: "Datasets", href: ROUTES.connections.datasets },
        { label: "Dataset Workspace" },
      )}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
        <DatasetWorkspaceContent datasetId={id} />
      </Suspense>
    </AnalyticsPageShell>
  );
}
