"use client";

import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { ErrorState } from "@/components/shared/error-state";
import { useSession } from "@/hooks/use-session";
import { ProfileIdentityCard, ProfileIdentityCardSkeleton } from "./profile-identity-card";

export const ProfilePage = () => {
  const { user, loading, error, refetch } = useSession();

  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Profile" },
  ];

  if (error) {
    return (
      <AnalyticsPageShell title="Profile" breadcrumbItems={breadcrumbItems}>
        <ErrorState message={error} onRetry={refetch} />
      </AnalyticsPageShell>
    );
  }

  return (
    <AnalyticsPageShell
      title="Profile"
      contextText={user ? user.email : undefined}
      breadcrumbItems={breadcrumbItems}
    >
      {loading ? (
        <ProfileIdentityCardSkeleton />
      ) : user ? (
        <ProfileIdentityCard user={user} />
      ) : null}
    </AnalyticsPageShell>
  );
}
