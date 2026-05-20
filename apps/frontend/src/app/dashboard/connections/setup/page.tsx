"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { SourceSetupWizard } from "@/components/data-studio/source-setup-wizard";

export default function SetupPage() {
  const searchParams = useSearchParams();
  const sourceKey = searchParams.get("source") || "static_file";

  const sourceLabel =
    sourceKey === "postgresql" ? "PostgreSQL"
    : sourceKey === "mysql" ? "MySQL"
    : "Static File";

  return (
    <AnalyticsPageShell
      title="Connection Setup"
      contextText={`Source: ${sourceLabel}`}
      actions={
        <Link
          href="/dashboard/connections/sources"
          className="rounded-md border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
        >
          Back to sources
        </Link>
      }
      breadcrumbItems={buildConnectionsBreadcrumbs(
        { label: "Source Catalog", href: "/dashboard/connections/sources" },
        { label: "Connection Setup" },
      )}
    >
      <SourceSetupWizard />
    </AnalyticsPageShell>
  );
}
