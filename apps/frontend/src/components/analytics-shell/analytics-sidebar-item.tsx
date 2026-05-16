"use client";

import Link from "next/link";
import type { ReactNode } from "react";

type Props = {
  href: string;
  icon: ReactNode;
  label: string;
  active: boolean;
  collapsed: boolean;
  onClick?: () => void;
};

export function AnalyticsSidebarItem({ href, icon, label, active, collapsed, onClick }: Props) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-zinc-100 text-zinc-900"
          : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900"
      } ${collapsed ? "justify-center px-2" : ""}`}
      title={collapsed ? label : undefined}
    >
      <span className="flex h-5 w-5 shrink-0 items-center justify-center">{icon}</span>
      {!collapsed && <span>{label}</span>}
    </Link>
  );
}
