"use client";

import type { ReactNode } from "react";
import { SessionGuard } from "./session-guard";
import { ToastProvider } from "@/components/shared";
import { AuthenticatedShell } from "@/components/authenticated-shell/authenticated-shell";
import { FeatureFlagsProvider } from "@/lib/feature-flags-context";

type Props = {
  children: ReactNode;
};

export const AuthenticatedAppLayout = ({ children }: Props) => {
  return (
    <SessionGuard>
      <ToastProvider>
        <FeatureFlagsProvider>
          <AuthenticatedShell>{children}</AuthenticatedShell>
        </FeatureFlagsProvider>
      </ToastProvider>
    </SessionGuard>
  );
}
