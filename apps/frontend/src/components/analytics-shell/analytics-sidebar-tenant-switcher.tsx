"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { useTenant } from "@/components/auth/session-guard";
import { switchTenant } from "@/lib/api/auth";

type Props = {
  collapsed: boolean;
};

export function AnalyticsSidebarTenantSwitcher({ collapsed }: Props) {
  const { tenant, tenants, refetch } = useTenant();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    if (!open) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  const handleSwitch = useCallback(
    async (tenantId: string) => {
      if (tenantId === tenant?.tenant_id) {
        setOpen(false);
        return;
      }
      setSwitching(true);
      setError(null);
      try {
        await switchTenant(tenantId);
        refetch();
        router.push("/dashboard");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Switch failed");
      } finally {
        setSwitching(false);
        setOpen(false);
      }
    },
    [tenant, refetch, router],
  );

  if (!tenant || tenants.length === 0) return null;

  const currentTenant = tenants.find((t) => t.tenant_id === tenant.tenant_id);

  if (collapsed) {
    return (
      <div ref={ref} className="px-2 py-2">
        <button
          onClick={() => setOpen(!open)}
          disabled={switching}
          className="flex w-full items-center justify-center rounded-lg px-2 py-2 text-sm font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
          title={currentTenant?.name ?? "Tenant"}
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-zinc-200 text-xs font-semibold text-zinc-700">
            {currentTenant?.name?.charAt(0).toUpperCase() ?? "T"}
          </span>
        </button>
        {open && (
          <div className="absolute bottom-full left-0 mb-1 w-48 rounded-lg border border-zinc-200 bg-white shadow-lg">
            {tenants.map((t) => (
              <button
                key={t.tenant_id}
                onClick={() => handleSwitch(t.tenant_id)}
                disabled={switching}
                className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors disabled:opacity-50 ${
                  t.tenant_id === tenant.tenant_id
                    ? "bg-zinc-100 font-medium text-zinc-900"
                    : "text-zinc-600 hover:bg-zinc-50"
                }`}
              >
                <span className="truncate">{t.name}</span>
                <span className="ml-auto text-xs text-zinc-400">{t.role}</span>
              </button>
            ))}
          </div>
        )}
        {error && (
          <p className="mt-1 text-xs text-red-600" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }

  return (
    <div ref={ref} className="border-t border-zinc-200 px-3 py-3">
      <button
        onClick={() => setOpen(!open)}
        disabled={switching}
        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50"
      >
        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded bg-zinc-200 text-xs font-semibold text-zinc-700">
          {currentTenant?.name?.charAt(0).toUpperCase() ?? "T"}
        </span>
        <span className="truncate">{currentTenant?.name ?? "Tenant"}</span>
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`ml-auto h-4 w-4 text-zinc-400 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>
      {open && (
        <div className="mt-1 rounded-lg border border-zinc-200 bg-white shadow-lg">
          {tenants.map((t) => (
            <button
              key={t.tenant_id}
              onClick={() => handleSwitch(t.tenant_id)}
              disabled={switching}
              className={`flex w-full items-center gap-2 px-3 py-2 text-left text-sm transition-colors disabled:opacity-50 ${
                t.tenant_id === tenant.tenant_id
                  ? "bg-zinc-100 font-medium text-zinc-900"
                  : "text-zinc-600 hover:bg-zinc-50"
              }`}
            >
              <span className="truncate">{t.name}</span>
              <span className="ml-auto text-xs text-zinc-400">{t.role}</span>
            </button>
          ))}
        </div>
      )}
      {error && (
        <p className="mt-1 text-xs text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
