"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/hooks/use-session";
import { ROUTES } from "@/lib/constants";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

const AdminLayout = ({ children }: { children: React.ReactNode }) => {
  const { user, loading } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (!loading && (!user || !user.is_admin)) {
      router.replace(ROUTES.dashboard);
    }
  }, [user, loading, router]);

  if (loading) {
    return <LoadingSpinner text="Checking access..." />;
  }

  if (!user?.is_admin) {
    return null;
  }

  return <>{children}</>;
};

export default AdminLayout;
