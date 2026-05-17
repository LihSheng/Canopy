import { Suspense } from "react";
import { DepartmentsPage as DepartmentsPageContent } from "@/components/departments/departments-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function DepartmentsPage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading departments..." />}>
      <DepartmentsPageContent />
    </Suspense>
  );
}
