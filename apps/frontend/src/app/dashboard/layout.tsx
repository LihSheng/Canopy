import { AuthenticatedAppLayout } from "@/components/auth/authenticated-app-layout";

const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
  return <AuthenticatedAppLayout>{children}</AuthenticatedAppLayout>;
}
export default DashboardLayout;
