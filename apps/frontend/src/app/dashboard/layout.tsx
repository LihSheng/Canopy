import { SessionGuard } from "@/components/auth/session-guard";
import { AnalyticsShell } from "@/components/analytics-shell/analytics-shell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionGuard>
      <AnalyticsShell>{children}</AnalyticsShell>
    </SessionGuard>
  );
}
