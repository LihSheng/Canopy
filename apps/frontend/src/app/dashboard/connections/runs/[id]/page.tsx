import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ROUTES, UI_LABELS } from "@/lib/constants";
import RunDetailContent from "./run-detail-content";

export default async function RunDetailPage(props: { params: Promise<{ id: string }> }) {
  const { id } = await props.params;
  return (
    <AnalyticsPageShell
      title="Run Detail"
      breadcrumbItems={buildConnectionsBreadcrumbs(
        { label: "Run History", href: ROUTES.connections.runs },
        { label: "Run Detail" },
      )}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
        <RunDetailContent runId={id} />
      </Suspense>
    </AnalyticsPageShell>
  );
}
