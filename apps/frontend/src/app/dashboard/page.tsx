import { Suspense } from "react";
import { DashboardShell } from "@/components/dashboard/dashboard-shell";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <Suspense fallback={<LoadingSpinner text="Loading dashboard..." />}>
        <DashboardShell />
      </Suspense>
    </div>
  );
}
