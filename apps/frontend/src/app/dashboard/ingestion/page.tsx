import { Suspense } from "react";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { IngestionPageContent } from "@/components/ingestion-v2/ingestion-page";

export default function IngestionPage() {
  return (
    <div>
      <AnalyticsHeader title="Ingestion" />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading..." />}>
          <IngestionPageContent />
        </Suspense>
      </div>
    </div>
  );
}
