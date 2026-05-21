import { Suspense } from "react";
import { AnomaliesPage as AnomaliesPageContent } from "@/components/anomalies/anomalies-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";

export default function AnomaliesPage() {
  return (
    <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
      <AnomaliesPageContent />
    </Suspense>
  );
}
