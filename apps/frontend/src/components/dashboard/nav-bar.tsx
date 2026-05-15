"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/hooks/use-session";
import { useRefreshPoller, RefreshStatusBadge } from "./refresh-widgets";

export function DashboardNav() {
  const { user, logout } = useSession();
  const pathname = usePathname();
  const { status } = useRefreshPoller(60000);

  const links = [
    { href: "/dashboard", label: "Overview" },
    { href: "/dashboard/anomalies", label: "Anomalies" },
  ];

  return (
    <nav className="sticky top-0 z-10 border-b border-zinc-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <Link href="/dashboard" className="text-sm font-semibold tracking-tight text-zinc-900">
            HERD Aggregator
          </Link>
          <div className="flex items-center gap-1">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  pathname === link.href
                    ? "bg-zinc-100 text-zinc-900"
                    : "text-zinc-500 hover:text-zinc-900"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          {status && <RefreshStatusBadge status={status.status} />}
          <span className="text-sm text-zinc-500">{user?.display_name}</span>
          <button
            onClick={logout}
            className="text-sm font-medium text-zinc-500 transition-colors hover:text-zinc-900"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  );
}
