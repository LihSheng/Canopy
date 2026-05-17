"use client";

import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { ErrorState } from "@/components/shared/error-state";
import { useSession } from "@/hooks/use-session";
import { ProfileIdentityCard, ProfileIdentityCardSkeleton } from "./profile-identity-card";

export function ProfilePage() {
  const { user, loading, error, refetch } = useSession();

  if (error) {
    return (
      <>
        <AnalyticsHeader title="Profile" />
        <AnalyticsBreadcrumb
          items={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Profile" },
          ]}
        />
        <div className="p-6">
          <ErrorState message={error} onRetry={refetch} />
        </div>
      </>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-auto">
      <AnalyticsHeader
        title="Profile"
        contextText={user ? user.email : undefined}
      />
      <AnalyticsBreadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Profile" },
        ]}
      />
      <div className="flex-1 overflow-auto p-6">
        {loading ? (
          <ProfileIdentityCardSkeleton />
        ) : user ? (
          <ProfileIdentityCard user={user} />
        ) : null}
      </div>
    </div>
  );
}
