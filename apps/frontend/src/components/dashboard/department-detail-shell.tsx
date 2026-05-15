"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { SummaryCard } from "./summary-card";
import { EmployeeContributionTable } from "./employee-contribution-table";
import { ClaimDetailTable } from "./claim-detail-table";
import { MonthFilter } from "./month-filter";
import { ErrorState } from "@/components/shared/error-state";
import { formatCurrency, formatPercent, getChangeColor } from "@/lib/formatters";
import {
  fetchDepartmentDetail,
  fetchEmployeeContributions,
  fetchClaimDetails,
} from "@/lib/api/dashboard";
import type { DepartmentDetail, EmployeeContribution, ClaimDetail } from "@/lib/api/types";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | {
      status: "success";
      department: DepartmentDetail;
      employees: EmployeeContribution[];
      claims: ClaimDetail[];
    };

export function DepartmentDetailShell({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const year = parseInt(searchParams.get("year") || String(new Date().getFullYear()), 10);
  const month = parseInt(searchParams.get("month") || String(new Date().getMonth() + 1), 10);

  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    const params = { year, month };
    try {
      const [department, employees, claims] = await Promise.all([
        fetchDepartmentDetail(id, params),
        fetchEmployeeContributions(id, params),
        fetchClaimDetails(id, params),
      ]);
      setData({ status: "success", department, employees, claims });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load department",
      });
    }
  }, [id, year, month]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch
    load();
  }, [load]);

  if (data.status === "error") {
    return (
      <>
        <Link
          href="/dashboard"
          className="mb-6 inline-flex text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
        >
          &larr; Back to Dashboard
        </Link>
        <ErrorState message={data.message} onRetry={load} />
      </>
    );
  }

  const loading = data.status === "loading";

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link
            href="/dashboard"
            className="mb-2 inline-flex text-sm font-medium text-zinc-500 hover:text-zinc-900 transition-colors"
          >
            &larr; Back to Dashboard
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
            {loading ? (
              <span className="inline-block h-7 w-48 animate-pulse rounded bg-zinc-100" />
            ) : (
              data.department.name
            )}
          </h1>
        </div>
        <MonthFilter />
      </div>

      {data.status === "success" && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <SummaryCard title="Total Spend">
              <p className="text-2xl font-semibold tracking-tight text-zinc-900">
                {formatCurrency(data.department.total_spend)}
              </p>
            </SummaryCard>
            <SummaryCard title="Payroll">
              <p className="text-2xl font-semibold tracking-tight text-zinc-900">
                {formatCurrency(data.department.payroll_spend)}
              </p>
            </SummaryCard>
            <SummaryCard title="Claims">
              <p className="text-2xl font-semibold tracking-tight text-zinc-900">
                {formatCurrency(data.department.claims_spend)}
              </p>
            </SummaryCard>
          </div>

          {data.department.change_pct !== undefined && (
            <p className={`text-sm font-medium ${getChangeColor(data.department.change_pct)}`}>
              {formatPercent(data.department.change_pct)} vs last month
            </p>
          )}
        </>
      )}

      {loading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl border border-zinc-200 bg-white p-6">
              <div className="h-3 w-20 animate-pulse rounded bg-zinc-100" />
              <div className="mt-3 h-8 w-28 animate-pulse rounded bg-zinc-100" />
            </div>
          ))}
        </div>
      )}

      <EmployeeContributionTable
        data={data.status === "success" ? data.employees : []}
        loading={loading}
      />

      <ClaimDetailTable
        data={data.status === "success" ? data.claims : []}
        loading={loading}
      />
    </div>
  );
}
