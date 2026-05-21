"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession } from "@/hooks/use-session";
import { ROUTES, UI_LABELS } from "@/lib/constants";

type Props = {
  collapsed: boolean;
  onNavigate?: () => void;
};

export function AnalyticsSidebarUtilities({ collapsed, onNavigate }: Props) {
  const { user, logout } = useSession();
  const pathname = usePathname();

  const profileActive = pathname === ROUTES.profile;

  return (
    <div className={`border-t border-zinc-200 ${collapsed ? "px-2 py-3" : "px-3 py-3"}`}>
      <div className="flex flex-col gap-1">
        <Link
          href={ROUTES.profile}
          onClick={onNavigate}
          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
            profileActive
              ? "bg-zinc-100 text-zinc-900"
              : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900"
          } ${collapsed ? "justify-center px-2" : ""}`}
          title={collapsed ? "Profile" : undefined}
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center">
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
            </svg>
          </span>
          {!collapsed && <span>Profile</span>}
        </Link>

        <button
          onClick={logout}
          className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-zinc-500 transition-colors hover:bg-zinc-50 hover:text-zinc-900 ${
            collapsed ? "justify-center px-2" : ""
          }`}
          title={collapsed ? UI_LABELS.signOut : undefined}
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center">
            <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
              <path
                fillRule="evenodd"
                d="M3 4.25A2.25 2.25 0 015.25 2h5.5A2.25 2.25 0 0113 4.25v2a.75.75 0 01-1.5 0v-2a.75.75 0 00-.75-.75h-5.5a.75.75 0 00-.75.75v11.5c0 .414.336.75.75.75h5.5a.75.75 0 00.75-.75v-2a.75.75 0 011.5 0v2A2.25 2.25 0 0110.75 18h-5.5A2.25 2.25 0 013 15.75V4.25z"
                clipRule="evenodd"
              />
              <path
                fillRule="evenodd"
                d="M6 10a.75.75 0 01.75-.75h9.546l-1.048-.943a.75.75 0 111.004-1.114l2.5 2.25a.75.75 0 010 1.114l-2.5 2.25a.75.75 0 11-1.004-1.114l1.048-.943H6.75A.75.75 0 016 10z"
                clipRule="evenodd"
              />
            </svg>
          </span>
          {!collapsed && <span>{user?.display_name ?? UI_LABELS.signOut}</span>}
        </button>
      </div>
    </div>
  );
}
