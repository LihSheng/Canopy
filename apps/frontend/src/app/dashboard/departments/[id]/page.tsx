import { Suspense } from "react";
import { DepartmentDetailShell } from "@/components/dashboard/department-detail-shell";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

export default async function DepartmentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <Suspense fallback={<LoadingSpinner text="Loading department..." />}>
        <DepartmentDetailShell id={id} />
      </Suspense>
    </div>
  );
}
