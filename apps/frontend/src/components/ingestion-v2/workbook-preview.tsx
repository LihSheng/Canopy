"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchPreview, type WorkbookProfile } from "@/lib/api/ingestion";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

type PreviewState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; profile: WorkbookProfile };

type Props = {
  uploadId: string;
};

function confidenceColor(confidence: number): string {
  if (confidence >= 0.7) return "text-green-600";
  if (confidence >= 0.4) return "text-amber-600";
  return "text-red-600";
}

export function WorkbookPreview({ uploadId }: Props) {
  const [state, setState] = useState<PreviewState>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const profile = await fetchPreview(uploadId);
      setState({ status: "success", profile });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load preview",
      });
    }
  }, [uploadId]);

  useEffect(() => {
    load();
  }, [load]);

  if (state.status === "loading") return <LoadingSpinner text="Profiling workbook..." />;
  if (state.status === "error") return <ErrorState message={state.message} onRetry={load} />;

  const { profile } = state;

  return (
    <div className="space-y-6">
      {profile.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm font-semibold text-amber-800">Warnings</p>
          <ul className="mt-1 list-inside list-disc text-sm text-amber-700">
            {profile.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        </div>
      )}

      <div>
        <h3 className="text-sm font-semibold text-zinc-700">Best Sheet</h3>
        <p className="text-sm text-zinc-500">{profile.best_sheet_name ?? "None"}</p>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-zinc-700">
          Columns ({profile.column_profiles.length})
        </h3>
        <div className="overflow-x-auto rounded-xl border border-zinc-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                <th className="px-3 py-2 font-medium text-zinc-500">Source Column</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Inferred Type</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Samples</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Null Ratio</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Confidence</th>
                <th className="px-3 py-2 font-medium text-zinc-500">Suggested Field</th>
              </tr>
            </thead>
            <tbody>
              {profile.column_profiles.map((col, i) => (
                <tr key={i} className="border-b border-zinc-100 last:border-0">
                  <td className="px-3 py-2 font-medium text-zinc-800">{col.source_column_name}</td>
                  <td className="px-3 py-2 text-zinc-600">{col.inferred_type}</td>
                  <td className="px-3 py-2 text-zinc-500">{col.sample_values.slice(0, 3).join(", ")}</td>
                  <td className="px-3 py-2 text-zinc-500">{(col.null_ratio * 100).toFixed(0)}%</td>
                  <td className={`px-3 py-2 font-medium ${confidenceColor(col.confidence)}`}>
                    {(col.confidence * 100).toFixed(0)}%
                  </td>
                  <td className="px-3 py-2 text-zinc-500">{col.suggested_target_field ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-semibold text-zinc-700">
          Preview Rows ({profile.preview_rows.length})
        </h3>
        <div className="overflow-x-auto rounded-xl border border-zinc-200">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-200 bg-zinc-50">
                {profile.column_profiles.map((col, i) => (
                  <th key={i} className="px-3 py-2 font-medium text-zinc-500">{col.source_column_name}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {profile.preview_rows.map((row, ri) => (
                <tr key={ri} className="border-b border-zinc-100 last:border-0">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-3 py-2 text-zinc-700">{cell ?? "—"}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
