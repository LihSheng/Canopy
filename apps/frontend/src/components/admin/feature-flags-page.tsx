"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchAllFlags,
  toggleFlag,
  type FeatureFlag,
} from "@/lib/api/feature-flags";
import { LoadingSpinner, ErrorState } from "@/components/shared";
import { useFeatureFlags } from "@/lib/feature-flags-context";
import { UI_LABELS } from "@/lib/constants";

export const FeatureFlagsPage = () => {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingKey, setTogglingKey] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const { refresh } = useFeatureFlags();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAllFlags();
      setFlags(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load feature flags"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleToggle = async (flagKey: string, currentEnabled: boolean) => {
    setTogglingKey(flagKey);
    setActionError(null);
    try {
      const updated = await toggleFlag(flagKey, !currentEnabled);
      setFlags((prev) =>
        prev.map((f) => (f.flag_key === flagKey ? updated : f))
      );
      refresh();
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Failed to toggle flag"
      );
    } finally {
      setTogglingKey(null);
    }
  };

  if (loading) {
    return <LoadingSpinner text={UI_LABELS.loadingFeatureFlags} />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={load} />;
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-zinc-500">
        Global rollout controls that affect all users. Managed by Admin role
        only.
      </p>

      {actionError && (
        <p className="text-sm text-rose-600">{actionError}</p>
      )}

      {flags.length === 0 ? (
        <div className="rounded-lg border border-zinc-200 bg-white p-8 text-center">
          <p className="text-sm text-zinc-500">
            No feature flags configured.
          </p>
        </div>
      ) : (
        <div className="rounded-lg border border-zinc-200 bg-white">
          <div className="divide-y divide-zinc-100">
            {flags.map((flag) => (
              <div
                key={flag.flag_key}
                className="flex items-center justify-between gap-4 px-4 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-900">
                    {flag.flag_key}
                  </p>
                  {flag.description && (
                    <p className="mt-0.5 text-xs text-zinc-500">
                      {flag.description}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={flag.enabled}
                  aria-label={`Toggle ${flag.flag_key}`}
                  disabled={togglingKey === flag.flag_key}
                  onClick={() => handleToggle(flag.flag_key, flag.enabled)}
                  className={`
                    relative inline-flex h-5 w-9 shrink-0 cursor-pointer
                    rounded-full border-2 border-transparent transition-colors
                    duration-200 ease-in-out focus:outline-none focus:ring-2
                    focus:ring-zinc-500 focus:ring-offset-2
                    disabled:cursor-wait disabled:opacity-50
                    ${flag.enabled ? "bg-zinc-900" : "bg-zinc-200"}
                  `}
                >
                  <span
                    className={`
                      pointer-events-none inline-block size-4 rounded-full
                      bg-white shadow ring-0 transition duration-200 ease-in-out
                      ${flag.enabled ? "translate-x-4" : "translate-x-0"}
                    `}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
