import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ConnectionWizard } from "@/components/data-studio/connection-wizard";

export default function NewConnectionPage() {
  return (
    <AnalyticsPageShell
      title="New Connection"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "New Connection" })}
    >
      <Suspense fallback={<LoadingSpinner text="Loading..." />}>
        <ConnectionWizard />
      </Suspense>
    </AnalyticsPageShell>
  );
}
