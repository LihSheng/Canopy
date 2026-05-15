import { SessionGuard } from "@/components/auth/session-guard";
import { DashboardNav } from "@/components/dashboard/nav-bar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SessionGuard>
      <div className="flex min-h-full flex-col">
        <DashboardNav />
        <main className="flex-1">{children}</main>
      </div>
    </SessionGuard>
  );
}
