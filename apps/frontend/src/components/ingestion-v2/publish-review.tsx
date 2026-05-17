"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchCleanedSnapshot,
  fetchMappings,
  fetchPublishHistory,
  fetchPublishState,
  publishUpload,
  type CleanedSnapshotResult,
  type MappingSuggestionsResult,
  type PublishHistory,
  type PublishRecord,
} from "@/lib/api/ingestion";
import { ErrorState } from "@/components/shared/error-state";

type Props = {
  uploadId: string;
};

type ValidationDisplay = {
  label: string;
  passed: boolean;
  type: "pass" | "warning" | "error";
  message?: string;
};

export function PublishReview({ uploadId }: Props) {
  const [snapshot, setSnapshot] = useState<CleanedSnapshotResult | null>(null);
  const [mappings, setMappings] = useState<MappingSuggestionsResult | null>(null);
  const [activePublish, setActivePublish] = useState<PublishRecord | null>(null);
  const [history, setHistory] = useState<PublishHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [validationChecks, setValidationChecks] = useState<ValidationDisplay[] | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [snap, mapping, state, hist] = await Promise.all([
        fetchCleanedSnapshot(uploadId).catch(() => null),
        fetchMappings(uploadId).catch(() => null),
        fetchPublishState(uploadId).catch(() => null),
        fetchPublishHistory(uploadId).catch(() => null),
      ]);
      setSnapshot(snap);
      setMappings(mapping);
      setActivePublish(state);
      setHistory(hist);
    } catch {
      // silently handle
    } finally {
      setLoading(false);
    }
  }, [uploadId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!snapshot || !mappings) return;
    const checks: ValidationDisplay[] = [];

    const confirmed = mappings.decisions.filter((d) => d.confirmed).length;
    const total = mappings.decisions.length;
    const requiredPresent = confirmed > 0;
    checks.push({
      label: "Mapping decisions confirmed",
      passed: requiredPresent,
      type: requiredPresent ? "pass" : "error",
      message: requiredPresent ? `${confirmed} of ${total} columns mapped` : "No confirmed mappings",
    });

    checks.push({
      label: "Cleaned snapshot status",
      passed: snapshot.status !== "failed",
      type: snapshot.status === "failed" ? "error" : snapshot.warning_count > 0 ? "warning" : "pass",
      message: snapshot.warning_count > 0
        ? `Completed with ${snapshot.warning_count} warnings`
        : `Status: ${snapshot.status}`,
    });

    if (snapshot.row_count > 0) {
      checks.push({
        label: "Non-empty result",
        passed: true,
        type: "pass",
        message: `${snapshot.row_count} rows`,
      });
    } else {
      checks.push({
        label: "Non-empty result",
        passed: false,
        type: "error",
        message: "Zero rows in cleaned output",
      });
    }

    setValidationChecks(checks);
  }, [snapshot, mappings]);

  const handlePublish = async () => {
    setPublishing(true);
    setPublishError(null);
    try {
      const result = await publishUpload(uploadId);
      setActivePublish(result);
      const hist = await fetchPublishHistory(uploadId);
      setHistory(hist);
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : "Publish failed");
    } finally {
      setPublishing(false);
    }
  };

  const hasBlockingErrors = validationChecks?.some((c) => c.type === "error" && !c.passed) ?? true;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <svg className="h-6 w-6 animate-spin text-zinc-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold text-zinc-700">Publish Review</h3>
        <p className="text-xs text-zinc-500">Review and activate the cleaned version for downstream use.</p>
      </div>

      {snapshot && (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 text-sm">
          <h4 className="mb-2 font-semibold text-zinc-800">Summary</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <span className="text-zinc-500">Row count:</span>
            <span className="font-medium text-zinc-800">{snapshot.row_count}</span>
            <span className="text-zinc-500">Warnings:</span>
            <span className="font-medium text-zinc-800">{snapshot.warning_count}</span>
            <span className="text-zinc-500">Template:</span>
            <span className="font-medium text-zinc-800">{snapshot.template_version_id}</span>
          </div>
        </div>
      )}

      {validationChecks && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Validation Checks</h4>
          {validationChecks.map((check, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm ${
                check.type === "error"
                  ? "border-red-200 bg-red-50 text-red-800"
                  : check.type === "warning"
                    ? "border-amber-200 bg-amber-50 text-amber-800"
                    : "border-emerald-200 bg-emerald-50 text-emerald-800"
              }`}
            >
              <span className="mt-0.5 shrink-0 text-base leading-none">
                {check.type === "error" ? "❌" : check.type === "warning" ? "⚠️" : "✅"}
              </span>
              <div>
                <span className="font-medium">{check.label}</span>
                {check.message && <p className="mt-0.5 text-xs opacity-80">{check.message}</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {activePublish ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm">
          <p className="font-semibold text-emerald-800">
            ✅ Published — version is active
          </p>
          <p className="mt-1 text-xs text-emerald-700">
            Published at: {activePublish.published_at ? new Date(activePublish.published_at).toLocaleString() : "N/A"}
          </p>
        </div>
      ) : (
        <button
          onClick={handlePublish}
          disabled={publishing || hasBlockingErrors}
          className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:opacity-50"
        >
          {publishing ? "Publishing..." : "Publish"}
        </button>
      )}

      {publishError && (
        <p className="text-sm text-red-600">{publishError}</p>
      )}

      {history && history.records.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Publish History</h4>
          <div className="space-y-1.5">
            {history.records.map((rec) => (
              <div
                key={rec.id}
                className="flex items-center justify-between rounded-lg border border-zinc-200 px-3 py-2 text-sm"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      rec.status === "active"
                        ? "bg-emerald-500"
                        : rec.status === "revoked"
                          ? "bg-zinc-400"
                          : "bg-amber-400"
                    }`}
                  />
                  <span className="font-medium text-zinc-800">{rec.status}</span>
                </div>
                <span className="text-xs text-zinc-500">
                  {rec.published_at ? new Date(rec.published_at).toLocaleString() : rec.created_at}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
