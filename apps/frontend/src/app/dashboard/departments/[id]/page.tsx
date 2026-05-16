import { Suspense } from "react";
import { DepartmentDetailPage } from "@/components/department-detail-v2/department-detail-page";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default async function DepartmentDetailRoute({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <Suspense fallback={<LoadingSpinner text="Loading department..." />}>
      <DepartmentDetailPage id={id} />
    </Suspense>
  );
}
