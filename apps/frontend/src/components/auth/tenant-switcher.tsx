"use client";

import { useState } from "react";

import { switchTenant } from "@/lib/api/auth";
import type { TenantInfo } from "@/lib/api/types";

interface TenantSwitcherProps {
  tenants: TenantInfo[];
  activeTenantId: string | null;
  onTenantSwitch: () => void;
}

export const TenantSwitcher = ({
  tenants,
  activeTenantId,
  onTenantSwitch,
}: TenantSwitcherProps) => {
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSwitch = async (tenantId: string) => {
    setSwitching(true);
    setError(null);
    try {
      await switchTenant(tenantId);
      onTenantSwitch();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to switch tenant"
      );
    } finally {
      setSwitching(false);
    }
  };

  if (tenants.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-medium text-zinc-700">
        Active Tenant
      </label>
      <div className="flex flex-wrap gap-2">
        {tenants.map((t) => (
          <button
            key={t.tenant_id}
            onClick={() => handleSwitch(t.tenant_id)}
            disabled={switching}
            className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
              t.tenant_id === activeTenantId
                ? "border-zinc-900 bg-zinc-900 text-white"
                : "border-zinc-300 text-zinc-700 hover:border-zinc-500"
            } disabled:opacity-50`}
          >
            {t.name} ({t.role})
          </button>
        ))}
      </div>
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
