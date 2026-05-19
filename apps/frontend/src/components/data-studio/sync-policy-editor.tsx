"use client";

import type { ColumnSchema } from "@/lib/api/types";

export type SyncMode = "batch" | "real_time" | "direct_query";
export type BatchStrategy = "full_snapshot" | "incremental_cursor";

export interface SyncPolicy {
  syncMode: SyncMode;
  batchStrategy: BatchStrategy;
  cursorColumn: string;
  frequencyMinutes: number;
}

export interface SyncPolicyEditorProps {
  tableName: string;
  schemaColumns: ColumnSchema[];
  detectedCursorColumn: string | null;
  value: SyncPolicy;
  onChange: (policy: SyncPolicy) => void;
}

const SYNC_MODE_OPTIONS: { value: SyncMode; label: string; description: string }[] = [
  { value: "batch", label: "Batch", description: "Scheduled pull on a timer" },
  { value: "real_time", label: "Real-Time", description: "Accelerated polling (future CDC)" },
  { value: "direct_query", label: "Direct View", description: "No copy — live queries only" },
];

const STRATEGY_OPTIONS: { value: BatchStrategy; label: string }[] = [
  { value: "full_snapshot", label: "Full Snapshot" },
  { value: "incremental_cursor", label: "Incremental Cursor" },
];

const FREQUENCY_OPTIONS: { value: number; label: string }[] = [
  { value: 60, label: "Every 1 hour" },
  { value: 360, label: "Every 6 hours" },
  { value: 720, label: "Every 12 hours" },
  { value: 1440, label: "Every 24 hours" },
  { value: 10080, label: "Every 7 days" },
];

export function SyncPolicyEditor({
  tableName,
  schemaColumns,
  detectedCursorColumn,
  value,
  onChange,
}: SyncPolicyEditorProps) {
  const cursorColumns = schemaColumns.filter((c) =>
    ["timestamp", "timestamptz", "datetime", "date"].some((t) =>
      c.data_type.toLowerCase().includes(t),
    ),
  );

  const hasAutoDetect = detectedCursorColumn != null;
  const showCursorWarning = !hasAutoDetect && cursorColumns.length === 0;

  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-4">
      <h4 className="mb-3 text-sm font-semibold text-zinc-900">{tableName}</h4>

      {/* Sync mode radio group */}
      <div className="mb-4">
        <label className="text-xs font-medium text-zinc-500">Sync mode</label>
        <div className="mt-1 flex gap-2">
          {SYNC_MODE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() =>
                onChange({
                  ...value,
                  syncMode: opt.value,
                  batchStrategy: opt.value === "batch" ? value.batchStrategy : "full_snapshot",
                })
              }
              className={`flex-1 rounded-md border px-3 py-2 text-left text-xs transition-colors ${
                value.syncMode === opt.value
                  ? "border-zinc-900 bg-zinc-900 text-white"
                  : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300"
              }`}
            >
              <div className="font-medium">{opt.label}</div>
              <div
                className={`mt-0.5 leading-tight ${
                  value.syncMode === opt.value ? "text-zinc-300" : "text-zinc-400"
                }`}
              >
                {opt.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Batch-specific settings */}
      {value.syncMode === "batch" && (
        <>
          {/* Batch strategy */}
          <div className="mb-4">
            <label className="text-xs font-medium text-zinc-500">Strategy</label>
            <div className="mt-1 flex gap-2">
              {STRATEGY_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => onChange({ ...value, batchStrategy: opt.value })}
                  className={`flex-1 rounded-md border px-3 py-2 text-xs font-medium transition-colors ${
                    value.batchStrategy === opt.value
                      ? "border-zinc-900 bg-zinc-100 text-zinc-900"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Frequency */}
          <div className="mb-4">
            <label className="text-xs font-medium text-zinc-500">Frequency</label>
            <select
              value={value.frequencyMinutes}
              onChange={(e) =>
                onChange({ ...value, frequencyMinutes: Number(e.target.value) })
              }
              className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 focus:border-zinc-400 focus:outline-none"
            >
              {FREQUENCY_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Cursor column */}
          {value.batchStrategy === "incremental_cursor" && (
            <div>
              <label className="flex items-center gap-1 text-xs font-medium text-zinc-500">
                Cursor column
                {hasAutoDetect && (
                  <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700">
                    auto-detected
                  </span>
                )}
                {!hasAutoDetect && cursorColumns.length > 0 && (
                  <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700">
                    manual
                  </span>
                )}
              </label>
              {showCursorWarning && (
                <p className="mb-1 text-xs text-amber-600">
                  No timestamp columns found. Select a column below or switch to Full Snapshot.
                </p>
              )}
              <select
                value={value.cursorColumn}
                onChange={(e) => onChange({ ...value, cursorColumn: e.target.value })}
                className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 focus:border-zinc-400 focus:outline-none"
              >
                {!hasAutoDetect && cursorColumns.length === 0 && (
                  <option value="">Select cursor column...</option>
                )}
                {cursorColumns.map((col) => (
                  <option key={col.name} value={col.name}>
                    {col.name} ({col.data_type})
                  </option>
                ))}
                {schemaColumns
                  .filter(
                    (c) =>
                      !cursorColumns.some((cc) => cc.name === c.name),
                  )
                  .map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name} ({col.data_type})
                    </option>
                  ))}
              </select>
            </div>
          )}
        </>
      )}

      {value.syncMode === "direct_query" && (
        <p className="text-xs text-zinc-400">
          Data will not be copied. Queries run live against the source database.
          Not available in dashboard, exports, or AI summaries.
        </p>
      )}

      {value.syncMode === "real_time" && (
        <p className="text-xs text-zinc-400">
          Currently uses accelerated polling. True CDC (streaming) support is planned.
        </p>
      )}
    </div>
  );
}
