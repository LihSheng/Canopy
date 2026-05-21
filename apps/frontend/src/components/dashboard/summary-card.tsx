import type { ReactNode } from "react";

export const SummaryCard = ({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) => {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {title}
      </h3>
      <div className="mt-3">{children}</div>
    </div>
  );
}
