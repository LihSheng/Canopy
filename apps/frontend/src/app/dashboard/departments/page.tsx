import { Suspense } from "react";
import { DepartmentsPage as DepartmentsPageContent } from "@/components/departments-v2/departments-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default function DepartmentsPage() {
  return (
    <Suspense fallback={<LoadingSpinner text="Loading departments..." />}>
      <DepartmentsPageContent />
    </Suspense>
  );
}
