import { Suspense } from "react";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import ConnectionsHomeContent from "./connections-home-content";

export default function ConnectionsPage() {
  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader title="Data Connections" />
      <div className="p-6">
        <Suspense fallback={<LoadingSpinner text="Loading connections..." />}>
          <ConnectionsHomeContent />
        </Suspense>
      </div>
    </div>
  );
}
