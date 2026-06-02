import { Suspense } from "react";
import { FeatureFlagsPage } from "@/components/admin/feature-flags-page";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ROUTES, UI_LABELS } from "@/lib/constants";

const FeatureFlagsRoute = () => {
  return (
    <AnalyticsPageShell
      title="Feature Flags"
      breadcrumbItems={[
        { label: "Dashboard", href: ROUTES.dashboard },
        { label: "Admin", href: ROUTES.admin.home },
        { label: "Feature Flags" },
      ]}
    >
      <Suspense fallback={<LoadingSpinner text={UI_LABELS.loadingFeatureFlags} />}>
        <FeatureFlagsPage />
      </Suspense>
    </AnalyticsPageShell>
  );
};

export default FeatureFlagsRoute;
