"use client";

import type { ReactNode } from "react";

type Props = {
  title: string;
  contextText?: string;
  actions?: ReactNode;
};

export const AnalyticsHeader = ({ title, contextText, actions }: Props) => {
  return (
    <header className="flex items-center justify-between border-b border-zinc-200 bg-white px-6 py-4">
      <div>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-900">{title}</h1>
        {contextText && (
          <p className="mt-0.5 text-sm text-zinc-500">{contextText}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </header>
  );
}
