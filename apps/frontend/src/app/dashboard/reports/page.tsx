import { Suspense } from "react";
import { ReportsPage as ReportsPageContent } from "@/components/reports/reports-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";

export default function ReportsPage() {
  return (
    <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
      <ReportsPageContent />
    </Suspense>
  );
}
