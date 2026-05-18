import { SessionGuard } from "@/components/auth/session-guard";
import { AnalyticsShell } from "@/components/analytics-shell/analytics-shell";
import { ToastProvider } from "@/components/shared";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionGuard>
      <ToastProvider>
        <AnalyticsShell>{children}</AnalyticsShell>
      </ToastProvider>
    </SessionGuard>
  );
}
