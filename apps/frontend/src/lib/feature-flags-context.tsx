"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { fetchEnabledFlags } from "@/lib/api/feature-flags";

interface FeatureFlagsContextValue {
  /** Map of flag_key -> enabled. Empty object while loading. */
  flags: Record<string, boolean>;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

const FeatureFlagsContext = createContext<FeatureFlagsContextValue>({
  flags: {},
  loading: true,
  error: null,
  refresh: () => {},
});

export const useFeatureFlags = () => useContext(FeatureFlagsContext);

export const FeatureFlagsProvider = ({ children }: { children: ReactNode }) => {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEnabledFlags();
      if (mountedRef.current) {
        setFlags(data);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(
          err instanceof Error ? err.message : "Failed to load feature flags"
        );
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    refresh();
    return () => {
      mountedRef.current = false;
    };
  }, [refresh]);

  return (
    <FeatureFlagsContext.Provider value={{ flags, loading, error, refresh }}>
      {children}
    </FeatureFlagsContext.Provider>
  );
};
