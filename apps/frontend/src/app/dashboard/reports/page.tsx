import { Suspense } from "react";
import { ReportsPage as ReportsPageContent } from "@/components/reports-v2/reports-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function ReportsPage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading reports..." />}>
      <ReportsPageContent />
    </Suspense>
  );
}
