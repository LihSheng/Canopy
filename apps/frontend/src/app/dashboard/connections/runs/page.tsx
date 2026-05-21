import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";
import RunsListContent from "./runs-list-content";

const RunsPage = () => {
  return (
    <AnalyticsPageShell
      title="Run History"
      contextText="All dataset processing runs"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Run History" })}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
        <RunsListContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
export default RunsPage;
