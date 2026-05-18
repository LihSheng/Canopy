"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";

import { TenantSwitcher } from "@/components/auth/tenant-switcher";
import { useSession } from "@/hooks/use-session";
import { getSession } from "@/lib/api/auth";
import type { TenantContextResponse, TenantInfo } from "@/lib/api/types";

interface SessionGuardProps {
  children: ReactNode;
}

interface TenantContextValue {
  tenant: TenantContextResponse | null;
  tenants: TenantInfo[];
  refetch: () => void;
}

const TenantCtx = createContext<TenantContextValue | null>(null);

export function useTenant(): TenantContextValue {
  const ctx = useContext(TenantCtx);
  if (!ctx) {
    throw new Error("useTenant must be used within SessionGuard");
  }
  return ctx;
}

export function SessionGuard({ children }: SessionGuardProps) {
  const { user, loading } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [tenant, setTenant] = useState<TenantContextResponse | null>(null);
  const [tenants, setTenants] = useState<TenantInfo[]>([]);
  const [sessionLoading, setSessionLoading] = useState(false);

  const fetchTenantInfo = useCallback(async () => {
    setSessionLoading(true);
    try {
      const session = await getSession();
      setTenant(session.tenant);
      setTenants(session.tenants);
    } catch {
      setTenant(null);
      setTenants([]);
    } finally {
      setSessionLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      fetchTenantInfo();
    }
  }, [user, fetchTenantInfo]);

  useEffect(() => {
    if (!loading && !user) {
      router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [loading, user, router, pathname]);

  if (loading || sessionLoading) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <p className="text-sm text-zinc-500">Loading session...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  if (tenants.length > 0 && !tenant) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center gap-8 px-4">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            Select a Tenant
          </h1>
          <p className="text-sm text-zinc-500">
            Choose the tenant you want to work with
          </p>
        </div>
        <TenantSwitcher
          tenants={tenants}
          activeTenantId={null}
          onTenantSwitch={fetchTenantInfo}
        />
      </div>
    );
  }

  return (
    <TenantCtx.Provider
      value={{ tenant, tenants, refetch: fetchTenantInfo }}
    >
      {children}
    </TenantCtx.Provider>
  );
}
