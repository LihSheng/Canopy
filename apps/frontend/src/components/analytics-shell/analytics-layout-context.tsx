"use client";

import {
  createContext,
  useCallback,
  useContext,
  useState,
  useSyncExternalStore,
} from "react";
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
  isNavigating: boolean;
  setIsNavigating: (v: boolean) => void;
};

const AnalyticsLayoutContext = createContext<LayoutContextValue | null>(null);

export const useAnalyticsLayout = () => {
  const ctx = useContext(AnalyticsLayoutContext);
  if (!ctx) {
    throw new Error(
      "useAnalyticsLayout must be used within AnalyticsLayoutProvider",
    );
  }
  return ctx;
};

const readCollapsed = (): boolean => {
  if (typeof window === "undefined") return false;
  try {
    return localStorage.getItem(STORAGE_KEY) === "true";
  } catch {
    return false;
  }
};

const writeCollapsed = (v: boolean) => {
  try {
    localStorage.setItem(STORAGE_KEY, String(v));
  } catch {
    // ignore
  }
};

export const AnalyticsLayoutProvider = ({
  children,
}: {
  children: ReactNode;
}) => {
  const [sidebarExpanded, setSidebarExpanded] = useState(
    () => !readCollapsed(),
  );
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);

  // On the server, isHydrated is false (no children rendered).
  // On the client after hydration, it switches to true.
  const isHydrated = useSyncExternalStore(
    () => () => {}, // subscribe – no external events to listen to
    () => true, // getSnapshot – client is always hydrated
    () => false, // getServerSnapshot – server is never hydrated
  );

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
        isNavigating,
        setIsNavigating,
      }}
    >
      {isHydrated ? children : null}
    </AnalyticsLayoutContext.Provider>
  );
};
