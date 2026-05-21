import type { SessionUser } from "@/lib/api/auth";

type Props = {
  user: SessionUser;
};

export const ProfileIdentityCard = ({ user }: Props) => {
  return (
    <div className="max-w-lg rounded-xl border border-zinc-200 bg-white p-6">
      <div className="flex items-center gap-4 mb-6">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-zinc-600">
          <svg viewBox="0 0 20 20" fill="currentColor" className="h-7 w-7">
            <path d="M10 8a3 3 0 100-6 3 3 0 000 6zM3.465 14.493a1.23 1.23 0 00.41 1.412A9.957 9.957 0 0010 18c2.31 0 4.438-.784 6.131-2.1.43-.333.604-.903.408-1.41a7.002 7.002 0 00-13.074.003z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-zinc-900">{user.display_name}</h2>
          <p className="text-sm text-zinc-500">{user.email}</p>
        </div>
      </div>

      <dl className="space-y-3">
        <div className="flex justify-between border-b border-zinc-100 pb-2">
          <dt className="text-sm text-zinc-500">User ID</dt>
          <dd className="text-sm font-medium text-zinc-900 font-mono">{user.id}</dd>
        </div>
        <div className="flex justify-between border-b border-zinc-100 pb-2">
          <dt className="text-sm text-zinc-500">Display name</dt>
          <dd className="text-sm font-medium text-zinc-900">{user.display_name}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-sm text-zinc-500">Email</dt>
          <dd className="text-sm font-medium text-zinc-900">{user.email}</dd>
        </div>
      </dl>
    </div>
  );
}

export const ProfileIdentityCardSkeleton = () => {
  return (
    <div className="max-w-lg rounded-xl border border-zinc-200 bg-white p-6 animate-pulse">
      <div className="flex items-center gap-4 mb-6">
        <div className="h-14 w-14 rounded-full bg-zinc-200" />
        <div className="space-y-2">
          <div className="h-5 w-32 rounded bg-zinc-200" />
          <div className="h-4 w-48 rounded bg-zinc-100" />
        </div>
      </div>
      <div className="space-y-3">
        <div className="flex justify-between border-b border-zinc-100 pb-2">
          <div className="h-4 w-14 rounded bg-zinc-100" />
          <div className="h-4 w-24 rounded bg-zinc-200" />
        </div>
        <div className="flex justify-between border-b border-zinc-100 pb-2">
          <div className="h-4 w-20 rounded bg-zinc-100" />
          <div className="h-4 w-32 rounded bg-zinc-200" />
        </div>
        <div className="flex justify-between">
          <div className="h-4 w-10 rounded bg-zinc-100" />
          <div className="h-4 w-40 rounded bg-zinc-200" />
        </div>
      </div>
    </div>
  );
}
