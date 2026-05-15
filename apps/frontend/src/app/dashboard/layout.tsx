import { SessionGuard } from "@/components/auth/session-guard";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <SessionGuard>{children}</SessionGuard>;
}
