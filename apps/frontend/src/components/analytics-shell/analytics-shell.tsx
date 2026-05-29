"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import {
  AnalyticsLayoutProvider,
  useAnalyticsLayout,
} from "./analytics-layout-context";
import { AnalyticsSidebar } from "./analytics-sidebar";
import { AnalyticsDrawer } from "./analytics-drawer";
import { useSession } from "@/hooks/use-session";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

const MIN_LOADING_MS = 400;

const ShellInner = ({ children }: { children: ReactNode }) => {
  const { openDrawer, isNavigating, setIsNavigating } = useAnalyticsLayout();
  const { user } = useSession();
  const pathname = usePathname();
  const prevPathname = useRef(pathname);
  const navStartTime = useRef(0);
  const hideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Record navigation start time when isNavigating flips to true.
  const prevIsNavigating = useRef(isNavigating);
  useEffect(() => {
    if (isNavigating && !prevIsNavigating.current) {
      navStartTime.current = Date.now();
    }
    prevIsNavigating.current = isNavigating;
  }, [isNavigating]);

  // When pathname changes, clear navigating with a minimum display duration.
  useEffect(() => {
    if (isNavigating && pathname !== prevPathname.current) {
      const elapsed = Date.now() - navStartTime.current;
      const remaining = MIN_LOADING_MS - elapsed;
      if (remaining <= 0) {
        setIsNavigating(false);
      } else {
        hideTimerRef.current = setTimeout(() => {
          setIsNavigating(false);
        }, remaining);
      }
    }
    prevPathname.current = pathname;

    return () => {
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current);
        hideTimerRef.current = null;
      }
    };
  }, [pathname, isNavigating, setIsNavigating]);

  return (
    <div className="flex h-dvh overflow-hidden bg-zinc-50">
      {/* Desktop sidebar */}
      <div className="hidden lg:block">
        <AnalyticsSidebar isAdmin={user?.is_admin ?? false} />
      </div>

      {/* Mobile drawer */}
      <AnalyticsDrawer />

      {/* Main content area — position relative so the loading overlay anchors inside */}
      <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
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

        {/* Page content always renders */}
        {children}

        {/* Loading overlay — sits on top of children, always centered */}
        {isNavigating && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-zinc-50">
            <LoadingSpinner text="Loading..." />
          </div>
        )}
      </div>
    </div>
  );
};

export const AnalyticsShell = ({ children }: { children: ReactNode }) => {
  return (
    <AnalyticsLayoutProvider>
      <ShellInner>{children}</ShellInner>
    </AnalyticsLayoutProvider>
  );
};
