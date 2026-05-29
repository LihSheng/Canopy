"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { switchTenant } from "@/lib/api/auth";
import { useSession } from "@/hooks/use-session";
import { getSession } from "@/lib/api/auth";
import type { TenantContextResponse, TenantInfo } from "@/lib/api/types";
import { ROUTES } from "@/lib/constants";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

interface SessionGuardProps {
  children: ReactNode;
}

interface TenantContextValue {
  tenant: TenantContextResponse | null;
  tenants: TenantInfo[];
  refetch: () => void;
}

const TenantCtx = createContext<TenantContextValue | null>(null);

export const useTenant = (): TenantContextValue => {
  const ctx = useContext(TenantCtx);
  if (!ctx) {
    throw new Error("useTenant must be used within SessionGuard");
  }
  return ctx;
};

export const SessionGuard = ({ children }: SessionGuardProps) => {
  const { user, loading } = useSession();
  const router = useRouter();
  const pathname = usePathname();
  const [tenant, setTenant] = useState<TenantContextResponse | null>(null);
  const [tenants, setTenants] = useState<TenantInfo[]>([]);
  const [sessionLoading, setSessionLoading] = useState(false);
  const autoEnterAttempted = useRef(false);

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
      // eslint-disable-next-line react-hooks/set-state-in-effect
      fetchTenantInfo();
    }
  }, [user, fetchTenantInfo]);

  // Auto-enter first tenant when authenticated but no tenant is active
  useEffect(() => {
    if (
      user &&
      tenants.length > 0 &&
      !tenant &&
      !sessionLoading &&
      !autoEnterAttempted.current
    ) {
      autoEnterAttempted.current = true;
      (async () => {
        try {
          await switchTenant(tenants[0].tenant_id);
          await fetchTenantInfo();
        } catch {
          // Auto-enter failed — leave tenant as null
        }
      })();
    }
  }, [user, tenants, tenant, sessionLoading, fetchTenantInfo]);

  useEffect(() => {
    if (!loading && !user) {
      router.push(`${ROUTES.login}?redirect=${encodeURIComponent(pathname)}`);
    }
  }, [loading, user, router, pathname]);

  if (loading || sessionLoading) {
    return (
      <div className="flex min-h-full items-center justify-center p-6">
        <LoadingSpinner text="Loading session..." />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <TenantCtx.Provider value={{ tenant, tenants, refetch: fetchTenantInfo }}>
      {children}
    </TenantCtx.Provider>
  );
};
