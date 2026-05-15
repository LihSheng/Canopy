import { Suspense } from "react";
import { AnomaliesShell } from "@/components/dashboard/anomalies-shell";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function AnomaliesPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <Suspense fallback={<LoadingSpinner text="Loading anomalies..." />}>
        <AnomaliesShell />
      </Suspense>
    </div>
  );
}
