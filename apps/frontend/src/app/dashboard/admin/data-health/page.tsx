import { Suspense } from "react";
import { DataHealthPageContent } from "@/components/admin/data-health-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

const DataHealthPage = () => {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading data health..." />}>
      <DataHealthPageContent />
    </Suspense>
  );
};
export default DataHealthPage;
