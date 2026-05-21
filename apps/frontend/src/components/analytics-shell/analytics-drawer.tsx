"use client";

import { useEffect } from "react";
import { AnalyticsSidebar } from "./analytics-sidebar";
import { useAnalyticsLayout } from "./analytics-layout-context";

export const AnalyticsDrawer = () => {
  const { mobileDrawerOpen, closeDrawer } = useAnalyticsLayout();

  useEffect(() => {
    if (mobileDrawerOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileDrawerOpen]);

  if (!mobileDrawerOpen) return null;

  return (
    <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
      <div
        className="fixed inset-0 bg-zinc-900/20 backdrop-blur-sm"
        onClick={closeDrawer}
        aria-hidden
      />
      <div className="fixed inset-y-0 left-0 z-50 flex">
        <AnalyticsSidebar onNavigate={closeDrawer} />
      </div>
    </div>
  );
}
