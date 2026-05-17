import { Suspense } from "react";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import SourceCatalogContent from "./source-catalog-content";

export default function SourcesPage() {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader
        title="Source Catalog"
        contextText="Browse and connect to available data sources"
      />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading source catalog..." />}>
          <SourceCatalogContent />
        </Suspense>
      </div>
    </div>
  );
}
