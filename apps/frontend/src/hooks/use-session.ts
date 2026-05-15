"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

import { getSession, type SessionUser } from "@/lib/api/auth";

export function useSession() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const checked = useRef(false);

  const checkSession = useCallback(async () => {
    if (checked.current) return;
    checked.current = true;
    setLoading(true);
    setError(null);
    try {
      const session = await getSession();
      if (session.authenticated && session.user) {
        setUser(session.user);
      } else {
        setUser(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Session check failed");
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial session fetch
    checkSession();
  }, [checkSession]);

  const logout = useCallback(async () => {
    const { logout: apiLogout } = await import("@/lib/api/auth");
    await apiLogout();
    setUser(null);
    router.push("/login");
  }, [router]);

  return { user, loading, error, refetch: checkSession, logout };
}
