import { Suspense } from "react";
import { DepartmentsPage as DepartmentsPageContent } from "@/components/departments/departments-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { UI_LABELS } from "@/lib/constants";

const DepartmentsPage = () => {
  return (
    <Suspense fallback={<LoadingSpinner text={UI_LABELS.loading} />}>
      <DepartmentsPageContent />
    </Suspense>
  );
}
export default DepartmentsPage;
