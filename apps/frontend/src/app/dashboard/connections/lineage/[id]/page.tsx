import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ROUTES, UI_LABELS } from "@/lib/constants";
import ConnectionLineageContent from "./connection-lineage-content";

const ConnectionLineagePage = async (props: { params: Promise<{ id: string }> }) => {
  const { id } = await props.params;
  return (
    <AnalyticsPageShell
      title="Connection Lineage"
      breadcrumbItems={buildConnectionsBreadcrumbs(
        { label: "Data Studio", href: ROUTES.connections.home },
        { label: "Lineage" },
      )}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
        <ConnectionLineageContent connectionId={id} />
      </Suspense>
    </AnalyticsPageShell>
  );
}

export default ConnectionLineagePage;

