import { Suspense } from "react";
import { DashboardPage as DashboardPageContent } from "@/components/dashboard-v2/dashboard-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function DashboardPage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading dashboard..." />}>
      <DashboardPageContent />
    </Suspense>
  );
}
