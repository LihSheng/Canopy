import { Suspense } from "react";
import { DepartmentDetailPage } from "@/components/department-detail/department-detail-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

const DepartmentDetailRoute = async ({
  params,
}: {
  params: Promise<{ id: string }>;
}) => {
  const { id } = await params;

  return (
    <Suspense fallback={<LoadingSpinner text="Loading department..." />}>
      <DepartmentDetailPage id={id} />
    </Suspense>
  );
};

export default DepartmentDetailRoute;
