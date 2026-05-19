"use client";

import type { ReactNode } from "react";
import { AnalyticsHeader } from "./analytics-header";
import { AnalyticsBreadcrumb } from "./analytics-breadcrumb";

export type BreadcrumbItem = {
  label: string;
  href?: string;
};

type Props =
  | {
      /** Simple header config — title is required for default header */
      title: string;
      contextText?: string;
      actions?: ReactNode;
      /** Custom header element overrides title/contextText/actions */
      header?: never;
      breadcrumbItems?: BreadcrumbItem[];
      children: ReactNode;
    }
  | {
      /** Custom header element replaces the default AnalyticsHeader */
      header: ReactNode;
      title?: never;
      contextText?: never;
      actions?: never;
      breadcrumbItems?: BreadcrumbItem[];
      children: ReactNode;
    };

/**
 * Shared page shell for all dashboard pages.
 *
 * Renders the AnalyticsHeader (or a custom header), optional breadcrumb,
 * and a scrollable padded content area — removing ~15 lines of boilerplate
 * from every page.
 */
export function AnalyticsPageShell(props: Props) {
  const { breadcrumbItems, children } = props;

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {"header" in props ? (
        props.header
      ) : (
        <AnalyticsHeader
          title={props.title}
          contextText={props.contextText}
          actions={props.actions}
        />
      )}

      {breadcrumbItems && breadcrumbItems.length > 0 && (
        <AnalyticsBreadcrumb items={breadcrumbItems} />
      )}

      <div className="flex-1 overflow-auto p-6">{children}</div>
    </div>
  );
}
