"use client";

import type { ReactNode } from "react";
import { AnalyticsLayoutProvider, useAnalyticsLayout } from "./analytics-layout-context";
import { AnalyticsSidebar } from "./analytics-sidebar";
import { AnalyticsDrawer } from "./analytics-drawer";

function ShellInner({ children }: { children: ReactNode }) {
  const { sidebarExpanded, openDrawer } = useAnalyticsLayout();

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <AnalyticsSidebar />
      </div>

      {/* Mobile drawer */}
      <AnalyticsDrawer />

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar with hamburger */}
        <div className="flex items-center gap-3 border-b border-zinc-200 bg-white px-4 py-2.5 lg:hidden">
          <button
            onClick={openDrawer}
            aria-label="Open navigation"
            className="flex h-8 w-8 items-center justify-center rounded-md text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900"
          >
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path
                fillRule="evenodd"
                d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zM2 10a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 10zm0 5.25a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75a.75.75 0 01-.75-.75z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <span className="text-sm font-semibold tracking-tight text-zinc-900">
            Canopy Intelligence
          </span>
        </div>

        {children}
      </div>
    </div>
  );
}

export function AnalyticsShell({ children }: { children: ReactNode }) {
  return (
    <AnalyticsLayoutProvider>
      <ShellInner>{children}</ShellInner>
    </AnalyticsLayoutProvider>
  );
}
