import { Suspense } from "react";
import { DashboardPage as DashboardPageContent } from "@/components/dashboard/dashboard-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

const DashboardPage = () => {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading dashboard..." />}>
      <DashboardPageContent />
    </Suspense>
  );
}
export default DashboardPage;
