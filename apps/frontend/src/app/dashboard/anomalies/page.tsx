import { Suspense } from "react";
import { AnomaliesPage as AnomaliesPageContent } from "@/components/anomalies-v2/anomalies-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function AnomaliesPage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading anomalies..." />}>
      <AnomaliesPageContent />
    </Suspense>
  );
}
