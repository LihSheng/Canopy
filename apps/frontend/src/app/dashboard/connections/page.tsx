import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import ConnectionsHomeContent from "./connections-home-content";

const ConnectionsPage = () => {
  return (
    <AnalyticsPageShell
      title="Data Studio"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Data Studio" })}
    >
      <Suspense fallback={<LoadingSpinner text="Loading..." />}>
        <ConnectionsHomeContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
export default ConnectionsPage;
