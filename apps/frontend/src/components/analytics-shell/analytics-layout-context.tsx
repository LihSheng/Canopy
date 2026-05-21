"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { LOCAL_STORAGE_KEYS } from "@/lib/constants";

const STORAGE_KEY = LOCAL_STORAGE_KEYS.sidebarCollapsed;

type LayoutContextValue = {
  sidebarExpanded: boolean;
  setSidebarExpanded: (v: boolean) => void;
  toggleSidebar: () => void;
  mobileDrawerOpen: boolean;
  setMobileDrawerOpen: (v: boolean) => void;
  openDrawer: () => void;
  closeDrawer: () => void;
};

const AnalyticsLayoutContext = createContext<LayoutContextValue | null>(null);

export function useAnalyticsLayout() {
  const ctx = useContext(AnalyticsLayoutContext);
  if (!ctx) {
    throw new Error("useAnalyticsLayout must be used within AnalyticsLayoutProvider");
  }
  return ctx;
}

function readCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function writeCollapsed(v: boolean) {
  try {
    localStorage.setItem(STORAGE_KEY, String(v));
  } catch {
    // ignore
  }
}

export function AnalyticsLayoutProvider({ children }: { children: ReactNode }) {
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setSidebarExpanded(!readCollapsed());
    setHydrated(true);
  }, []);

  const toggleSidebar = useCallback(() => {
    setSidebarExpanded((prev) => {
      const next = !prev;
      writeCollapsed(!next);
      return next;
    });
  }, []);

  const openDrawer = useCallback(() => setMobileDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setMobileDrawerOpen(false), []);

  return (
    <AnalyticsLayoutContext.Provider
      value={{
        sidebarExpanded,
        setSidebarExpanded,
        toggleSidebar,
        mobileDrawerOpen,
        setMobileDrawerOpen,
        openDrawer,
        closeDrawer,
      }}
    >
      {hydrated ? children : null}
    </AnalyticsLayoutContext.Provider>
  );
}
