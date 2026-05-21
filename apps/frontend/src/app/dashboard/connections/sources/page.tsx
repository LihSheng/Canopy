import { Suspense } from "react";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";
import SourceCatalogContent from "./source-catalog-content";

export default function SourcesPage() {
  return (
    <AnalyticsPageShell
      title="Source Catalog"
      contextText="Browse and connect to available data sources"
      breadcrumbItems={buildConnectionsBreadcrumbs({ label: "Source Catalog" })}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
        <SourceCatalogContent />
      </Suspense>
    </AnalyticsPageShell>
  );
}
