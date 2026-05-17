import type { BreadcrumbItem } from "@/components/analytics-shell/analytics-breadcrumb";

const DASHBOARD_ITEM: BreadcrumbItem = { label: "Dashboard", href: "/dashboard" };
const CONNECTIONS_ITEM: BreadcrumbItem = {
  label: "Data Connections",
  href: "/dashboard/connections",
};

export function buildConnectionsBreadcrumbs(...items: BreadcrumbItem[]): BreadcrumbItem[] {
  return [DASHBOARD_ITEM, CONNECTIONS_ITEM, ...items];
}
