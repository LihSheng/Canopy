import type { BreadcrumbItem } from "@/components/analytics-shell/analytics-breadcrumb";

const DASHBOARD_ITEM: BreadcrumbItem = { label: "Dashboard", href: "/dashboard" };
const CONNECTIONS_ITEM: BreadcrumbItem = {
  label: "Data Studio",
  href: "/dashboard/connections",
};

export const buildConnectionsBreadcrumbs = (...items: BreadcrumbItem[]): BreadcrumbItem[] => {
  return [DASHBOARD_ITEM, CONNECTIONS_ITEM, ...items];
}
