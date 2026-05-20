import { AuthenticatedAppLayout } from "@/components/auth/authenticated-app-layout";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return <AuthenticatedAppLayout>{children}</AuthenticatedAppLayout>;
}
