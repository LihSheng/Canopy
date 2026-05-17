"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  type ColumnProfile,
  type MappingDecision,
  fetchMappings,
  saveMapping,
} from "@/lib/api/ingestion";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

type GridState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "idle"; decisions: EditableDecision[]; columnProfiles: ColumnProfile[] }
  | { status: "saving" }
  | { status: "saved" };

type EditableDecision = {
  source_column_name: string;
  target_field_name: string;
  confirmed: boolean;
  overridden_by_user: boolean;
  confidence: number;
  suggested_target_field: string | null;
  sample_values: string[];
  required: boolean;
};

type Props = {
  uploadId: string;
  onMappingsSaved?: () => void;
};

const REQUIRED_PATTERNS = /employee_id|name|full_name|amount|salary|payroll|date|department|email|claim_type/i;

const COMMON_TARGETS = [
  "employee_id",
  "employee_name",
  "full_name",
  "department",
  "amount",
  "salary",
  "currency",
  "date",
  "period",
  "claim_type",
  "status",
  "email",
  "payroll_month",
];

function isRequired(source_column_name: string): boolean {
  return REQUIRED_PATTERNS.test(source_column_name);
}

function confidenceBadge(confidence: number): { label: string; class: string } {
  if (confidence >= 0.7) return { label: "High", class: "bg-green-100 text-green-700" };
  if (confidence >= 0.4) return { label: "Medium", class: "bg-amber-100 text-amber-700" };
  return { label: "Low", class: "bg-red-100 text-red-700" };
}

function buildInitialDecisions(columnProfiles: ColumnProfile[]): EditableDecision[] {
  return columnProfiles.map((col) => ({
    source_column_name: col.source_column_name,
    target_field_name: col.suggested_target_field ?? "",
    confirmed: col.confidence >= 0.7,
    overridden_by_user: false,
    confidence: col.confidence,
    suggested_target_field: col.suggested_target_field,
    sample_values: col.sample_values,
    required: isRequired(col.source_column_name),
  }));
}

export function MappingReviewGrid({ uploadId, onMappingsSaved }: Props) {
  const [state, setState] = useState<GridState>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const result = await fetchMappings(uploadId);
      const profiles = result.column_profiles.length > 0
        ? result.column_profiles
        : result.decisions.map((d) => ({
            source_column_name: d.source_column_name,
            inferred_type: "text",
            sample_values: [] as string[],
            null_ratio: 0,
            confidence: d.confirmed ? 0.8 : 0.3,
            suggested_target_field: d.target_field_name || null,
          }));
      setState({
        status: "idle",
        decisions: buildInitialDecisions(profiles),
        columnProfiles: profiles,
      });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load mappings",
      });
    }
  }, [uploadId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleTargetChange = useCallback(
    (sourceColumnName: string, newTarget: string) => {
      setState((prev) => {
        if (prev.status !== "idle") return prev;
        return {
          ...prev,
          decisions: prev.decisions.map((d) =>
            d.source_column_name === sourceColumnName
              ? {
                  ...d,
                  target_field_name: newTarget,
                  overridden_by_user: newTarget !== (d.suggested_target_field ?? ""),
                  confirmed: newTarget !== "",
                }
              : d,
          ),
        };
      });
    },
    [],
  );

  const handleBulkApply = useCallback(() => {
    setState((prev) => {
      if (prev.status !== "idle") return prev;
      return {
        ...prev,
        decisions: prev.decisions.map((d) =>
          d.confidence >= 0.7
            ? { ...d, target_field_name: d.suggested_target_field ?? "", confirmed: true }
            : d,
        ),
      };
    });
  }, []);

  const handleSave = useCallback(async () => {
    if (state.status !== "idle") return;
    setState({ ...state, status: "saving" });
    try {
      const decisions: MappingDecision[] = state.decisions.map((d) => ({
        source_column_name: d.source_column_name,
        target_field_name: d.target_field_name,
        confirmed: d.confirmed,
        overridden_by_user: d.overridden_by_user,
      }));
      await saveMapping(uploadId, decisions);
      setState({ ...state, status: "saved" });
      onMappingsSaved?.();
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to save mappings",
      });
    }
  }, [state, uploadId, onMappingsSaved]);

  const unmappedRequired = useMemo(() => {
    if (state.status !== "idle") return [];
    return state.decisions.filter((d) => d.required && d.target_field_name === "");
  }, [state]);

  const hasHighConfidence = useMemo(() => {
    if (state.status !== "idle") return false;
    return state.decisions.some((d) => d.confidence >= 0.7 && d.suggested_target_field);
  }, [state]);

  if (state.status === "loading") return <LoadingSpinner text="Loading mapping suggestions..." />;
  if (state.status === "error") return <ErrorState message={state.message} onRetry={load} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Column Mapping Review</h3>
        <div className="flex gap-2">
          {hasHighConfidence && (
            <button
              onClick={handleBulkApply}
              className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-blue-500"
            >
              Bulk Apply High-Confidence
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={state.status === "saving" || unmappedRequired.length > 0}
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {state.status === "saving" ? "Saving..." : state.status === "saved" ? "Saved" : "Save Mappings"}
          </button>
        </div>
      </div>

      {unmappedRequired.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3">
          <p className="text-sm font-semibold text-red-800">
            {unmappedRequired.length} required field{unmappedRequired.length > 1 ? "s" : ""} unmapped
          </p>
          <ul className="mt-1 list-inside list-disc text-sm text-red-700">
            {unmappedRequired.map((d) => (
              <li key={d.source_column_name}>{d.source_column_name}</li>
            ))}
          </ul>
        </div>
      )}

      {state.status === "saved" && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-3">
          <p className="text-sm font-semibold text-green-800">Mapping decisions saved.</p>
        </div>
      )}

      <div className="overflow-x-auto rounded-xl border border-zinc-200">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-zinc-200 bg-zinc-50">
              <th className="px-3 py-2 font-medium text-zinc-500">Source Column</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Target Field</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Confidence</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Sample Values</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Required</th>
              <th className="px-3 py-2 font-medium text-zinc-500">Override</th>
            </tr>
          </thead>
          <tbody>
            {state.decisions.map((dec, i) => {
              const badge = confidenceBadge(dec.confidence);
              return (
                <tr
                  key={dec.source_column_name}
                  className={`border-b border-zinc-100 last:border-0 ${
                    dec.required && dec.target_field_name === "" ? "bg-red-50" : ""
                  }`}
                >
                  <td className="px-3 py-2 font-medium text-zinc-800">
                    {dec.source_column_name}
                  </td>
                  <td className="px-3 py-2">
                    <select
                      value={dec.target_field_name}
                      onChange={(e) => handleTargetChange(dec.source_column_name, e.target.value)}
                      className={`w-full rounded border px-2 py-1 text-sm ${
                        dec.overridden_by_user
                          ? "border-blue-400 bg-blue-50 text-blue-800"
                          : "border-zinc-300 bg-white text-zinc-800"
                      }`}
                    >
                      <option value="">-- Select target --</option>
                      {COMMON_TARGETS.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                      {dec.suggested_target_field && !COMMON_TARGETS.includes(dec.suggested_target_field) && (
                        <option key={dec.suggested_target_field} value={dec.suggested_target_field}>
                          {dec.suggested_target_field}
                        </option>
                      )}
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${badge.class}`}>
                      {badge.label} ({(dec.confidence * 100).toFixed(0)}%)
                    </span>
                  </td>
                  <td className="max-w-[200px] truncate px-3 py-2 text-zinc-500">
                    {dec.sample_values.slice(0, 3).join(", ") || "—"}
                  </td>
                  <td className="px-3 py-2">
                    {dec.required ? (
                      <span className="inline-block rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                        Required
                      </span>
                    ) : (
                      <span className="inline-block rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                        Optional
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {dec.overridden_by_user ? (
                      <span className="inline-block rounded bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700">
                        Overridden
                      </span>
                    ) : (
                      <span className="text-xs text-zinc-400">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
