"use client";

import type { ReactNode } from "react";
import { SessionGuard } from "./session-guard";
import { ToastProvider } from "@/components/shared";
import { AuthenticatedShell } from "@/components/authenticated-shell/authenticated-shell";

type Props = {
  children: ReactNode;
};

export const AuthenticatedAppLayout = ({ children }: Props) => {
  return (
    <SessionGuard>
      <ToastProvider>
        <AuthenticatedShell>{children}</AuthenticatedShell>
      </ToastProvider>
    </SessionGuard>
  );
}
