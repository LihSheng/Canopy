"use client";

import { usePathname } from "next/navigation";
import { AnalyticsSidebarBrand } from "./analytics-sidebar-brand";
import { AnalyticsSidebarItem } from "./analytics-sidebar-item";
import { AnalyticsSidebarTenantSwitcher } from "./analytics-sidebar-tenant-switcher";
import { AnalyticsSidebarUtilities } from "./analytics-sidebar-utilities";
import { useAnalyticsLayout } from "./analytics-layout-context";

import { ROUTES } from "@/lib/constants";

const ITEMS = [
  {
    href: ROUTES.dashboard,
    label: "Dashboard",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path
          fillRule="evenodd"
          d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-3a1 1 0 00-1-1H9a1 1 0 00-1 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    href: ROUTES.anomalies,
    label: "Anomalies",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path
          fillRule="evenodd"
          d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    href: ROUTES.departments,
    label: "Departments",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path d="M3.196 12.87l-.825.483a.75.75 0 000 1.294l7.25 4.25a.75.75 0 00.758 0l7.25-4.25a.75.75 0 000-1.294l-.825-.484-5.666 3.322a2.25 2.25 0 01-2.276 0L3.196 12.87z" />
        <path d="M3.196 8.87l-.825.483a.75.75 0 000 1.294l7.25 4.25a.75.75 0 00.758 0l7.25-4.25a.75.75 0 000-1.294l-.825-.484-5.666 3.322a2.25 2.25 0 01-2.276 0L3.196 8.87z" />
        <path d="M10.38 1.103a.75.75 0 00-.76 0l-7.25 4.25a.75.75 0 000 1.294l7.25 4.25a.75.75 0 00.76 0l7.25-4.25a.75.75 0 000-1.294l-7.25-4.25z" />
      </svg>
    ),
  },
  {
    href: ROUTES.reports,
    label: "Reports",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path
          fillRule="evenodd"
          d="M4.5 2A1.5 1.5 0 003 3.5v13A1.5 1.5 0 004.5 18h11a1.5 1.5 0 001.5-1.5V7.621a1.5 1.5 0 00-.44-1.06l-4.12-4.122A1.5 1.5 0 0011.378 2H4.5zm2.25 8.5a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5zm0 3a.75.75 0 000 1.5h6.5a.75.75 0 000-1.5h-6.5z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    href: ROUTES.connections.home,
    label: "Data Studio",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
      </svg>
    ),
  },
];

const ADMIN_ITEMS = [
  {
    href: ROUTES.admin.dataHealth,
    label: "Data Health",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path
          fillRule="evenodd"
          d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    href: ROUTES.admin.featureFlags,
    label: "Feature Flags",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
        <path
          fillRule="evenodd"
          d="M3.5 2A1.5 1.5 0 002 3.5v13A1.5 1.5 0 003.5 18h13a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-.44-1.06l-3.56-3.56A1.5 1.5 0 0012.94 1H6.5A1.5 1.5 0 005 2.5v2a.75.75 0 001.5 0v-2A.75.75 0 005 1.5h6.94l.12.06.09.09 3.56 3.56.06.12v.17h.04V4h.01v9.5a.75.75 0 01-.75.75H4.75A.75.75 0 014 13.5V4a.75.75 0 01.75-.75h2a.75.75 0 000-1.5h-2z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
];

type Props = {
  onNavigate?: () => void;
  isAdmin?: boolean;
};

export const AnalyticsSidebar = ({ onNavigate, isAdmin = false }: Props) => {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar, setIsNavigating } =
    useAnalyticsLayout();

  const isActive = (href: string) =>
    href === ROUTES.dashboard
      ? pathname === ROUTES.dashboard
      : pathname.startsWith(href);

  const allItems = isAdmin ? [...ITEMS, ...ADMIN_ITEMS] : ITEMS;

  return (
    <aside
      className={`flex h-full flex-col border-r border-zinc-200 bg-white transition-all duration-200 ${
        sidebarExpanded ? "w-56" : "w-[56px]"
      }`}
    >
      <AnalyticsSidebarBrand collapsed={!sidebarExpanded} />

      <div className="flex items-center justify-end px-2 py-2">
        <button
          onClick={toggleSidebar}
          aria-label={sidebarExpanded ? "Collapse sidebar" : "Expand sidebar"}
          className="flex h-7 w-7 items-center justify-center rounded-md text-zinc-400 transition-colors hover:bg-zinc-100 hover:text-zinc-600"
        >
          <svg
            viewBox="0 0 20 20"
            fill="currentColor"
            className={`h-4 w-4 transition-transform ${sidebarExpanded ? "" : "rotate-180"}`}
          >
            <path
              fillRule="evenodd"
              d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-2">
        {allItems.map((item) => (
          <AnalyticsSidebarItem
            key={item.href}
            href={item.href}
            icon={item.icon}
            label={item.label}
            active={isActive(item.href)}
            collapsed={!sidebarExpanded}
            onClick={() => {
              onNavigate?.();
              if (!isActive(item.href)) {
                setIsNavigating(true);
              }
            }}
          />
        ))}
      </nav>

      <AnalyticsSidebarTenantSwitcher collapsed={!sidebarExpanded} />
      <AnalyticsSidebarUtilities
        collapsed={!sidebarExpanded}
        onNavigate={onNavigate}
      />
    </aside>
  );
};
