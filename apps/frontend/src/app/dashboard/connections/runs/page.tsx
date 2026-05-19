import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import RunsListContent from "./runs-list-content";

export default function RunsPage() {
  return (
    <AnalyticsPageShell
      title="Run History"
      contextText="All dataset processing runs"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Run History" })}
    >
      <Suspense fallback={<LoadingSpinner text="Loading runs..." />}>
        <RunsListContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
