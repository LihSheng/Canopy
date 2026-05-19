import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import ConnectionsHomeContent from "./connections-home-content";

export default function ConnectionsPage() {
  return (
    <AnalyticsPageShell
      title="Data Connections"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Data Connections" })}
    >
      <Suspense fallback={<LoadingSpinner text="Loading connections..." />}>
        <ConnectionsHomeContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
