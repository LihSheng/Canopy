"use client";

import Link from "next/link";
import { BRAND, ROUTES } from "@/lib/constants";

type Props = {
  collapsed: boolean;
};

export function AnalyticsSidebarBrand({ collapsed }: Props) {
  return (
    <div
      className={`flex items-center border-b border-zinc-200 px-3 ${
        collapsed ? "h-14 justify-center" : "h-14 gap-3"
      }`}
    >
      <Link
        href={ROUTES.dashboard}
        className="flex items-center gap-2 font-semibold tracking-tight text-zinc-900"
      >
        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-zinc-900 text-xs font-bold text-white">
          C
        </span>
        {!collapsed && <span className="text-sm">{BRAND.name}</span>}
      </Link>
    </div>
  );
}
