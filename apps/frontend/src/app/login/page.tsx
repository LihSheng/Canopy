"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import { LoginForm } from "@/components/auth/login-form";
import { login } from "@/lib/api/auth";
import { BRAND, ROUTES, ERROR_MESSAGES } from "@/lib/constants";

const LoginPage = () => {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = useCallback(
    async (email: string, password: string) => {
      setError(null);
      setLoading(true);
      try {
        await login({ email, password });
        router.push(ROUTES.dashboard);
      } catch (err) {
        setError(err instanceof Error ? err.message : ERROR_MESSAGES.loginFailed);
      } finally {
        setLoading(false);
      }
    },
    [router],
  );

  return (
    <div className="flex min-h-full flex-col items-center justify-center px-4">
      <div className="flex w-full max-w-sm flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            {BRAND.name}
          </h1>
          <p className="text-sm text-zinc-500">
            Sign in to your account
          </p>
        </div>

        <LoginForm onSubmit={handleLogin} error={error} loading={loading} />
      </div>
    </div>
  );
}
export default LoginPage;
