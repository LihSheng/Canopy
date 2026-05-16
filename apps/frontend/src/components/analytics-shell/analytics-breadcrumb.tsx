"use client";

import Link from "next/link";
import { Fragment } from "react";

type BreadcrumbItem = {
  label: string;
  href?: string;
};

type Props = {
  items: BreadcrumbItem[];
};

export function AnalyticsBreadcrumb({ items }: Props) {
  return (
    <nav aria-label="Breadcrumb" className="px-6 pt-4">
      <ol className="flex items-center gap-1.5 text-sm text-zinc-500">
        {items.map((item, i) => {
          const isLast = i === items.length - 1;
          return (
            <Fragment key={`${item.label}-${i}`}>
              <li>
                {isLast || !item.href ? (
                  <span className="text-zinc-400">{item.label}</span>
                ) : (
                  <Link href={item.href} className="transition-colors hover:text-zinc-900">
                    {item.label}
                  </Link>
                )}
              </li>
              {!isLast && (
                <li aria-hidden>
                  <svg viewBox="0 0 20 20" fill="currentColor" className="h-4 w-4 text-zinc-300">
                    <path
                      fillRule="evenodd"
                      d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                      clipRule="evenodd"
                    />
                  </svg>
                </li>
              )}
            </Fragment>
          );
        })}
      </ol>
    </nav>
  );
}
