"use client";

import type { ColumnSchema } from "@/lib/api/types";

export type SyncMode = "batch" | "real_time" | "direct_query";
export type BatchStrategy = "full_snapshot" | "incremental_cursor";
export type RealTimeStrategy = "cdc" | "polling";

export interface SyncPolicy {
  syncMode: SyncMode;
  batchStrategy: BatchStrategy;
  realTimeStrategy?: RealTimeStrategy;
  cursorColumn: string;
  frequencyMinutes: number;
}

export interface SyncPolicyEditorProps {
  tableName: string;
  schemaColumns: ColumnSchema[];
  detectedCursorColumn: string | null;
  value: SyncPolicy;
  onChange: (policy: SyncPolicy) => void;
  supportsCdc?: boolean;
  sourceType?: string;
}

const SYNC_MODE_OPTIONS: { value: SyncMode; label: string; description: string }[] = [
  { value: "batch", label: "Batch", description: "Scheduled pull on a timer" },
  { value: "real_time", label: "Real-Time", description: "CDC for supported sources, polling fallback otherwise" },
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
  supportsCdc = false,
  sourceType,
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
              onClick={() => {
                const nextPolicy: SyncPolicy = {
                  ...value,
                  syncMode: opt.value,
                  batchStrategy: opt.value === "batch" ? value.batchStrategy : "full_snapshot",
                  realTimeStrategy:
                    opt.value === "real_time"
                      ? value.realTimeStrategy ?? (supportsCdc ? "cdc" : "polling")
                      : value.realTimeStrategy,
                };
                onChange(nextPolicy);
              }}
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
        <>
          {/* Real-time strategy selection */}
          <div className="mb-4">
            <label className="text-xs font-medium text-zinc-500">Real-Time Strategy</label>
            <div className="mt-1 flex gap-2">
              <button
                type="button"
                disabled={!supportsCdc}
                onClick={() => onChange({ ...value, realTimeStrategy: "cdc" })}
                className={`flex-1 rounded-md border px-3 py-2.5 text-xs font-medium transition-colors text-left relative ${
                  value.realTimeStrategy === "cdc" && supportsCdc
                    ? "border-zinc-900 bg-zinc-900 text-white"
                    : !supportsCdc
                    ? "border-zinc-100 bg-zinc-50 text-zinc-400 cursor-not-allowed"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                }`}
              >
                <div className="font-semibold flex items-center justify-between">
                  <span>True CDC (Streaming)</span>
                  {supportsCdc && (
                    <span className="rounded bg-emerald-500 px-1.5 py-0.5 text-[9px] font-semibold text-white">
                      Active
                    </span>
                  )}
                </div>
                <div className="mt-1 text-[11px] leading-normal font-normal opacity-90">
                  Continuous log-based replication. Low database load.
                </div>
              </button>

              <button
                type="button"
                onClick={() => onChange({ ...value, realTimeStrategy: "polling" })}
                className={`flex-1 rounded-md border px-3 py-2.5 text-xs font-medium transition-colors text-left ${
                  value.realTimeStrategy === "polling" || !supportsCdc
                    ? "border-zinc-900 bg-zinc-900 text-white"
                    : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300"
                }`}
              >
                <div className="font-semibold flex items-center justify-between">
                  <span>Accelerated Polling</span>
                  {(!supportsCdc || value.realTimeStrategy === "polling") && (
                    <span className="rounded bg-amber-500 px-1.5 py-0.5 text-[9px] font-semibold text-white">
                      Active
                    </span>
                  )}
                </div>
                <div className="mt-1 text-[11px] leading-normal font-normal opacity-90">
                  Frequent polling queries. Fallback for standard databases.
                </div>
              </button>
            </div>
          </div>

          {/* Sleek Alert Warning for unsupported CDC */}
          {!supportsCdc && (
            <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3.5 text-xs text-amber-900 shadow-sm animate-in fade-in slide-in-from-top-1 duration-250">
              <div className="flex items-center gap-1.5 font-semibold text-amber-800">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="h-4 w-4 text-amber-600"
                >
                  <path
                    fillRule="evenodd"
                    d="M8.485 2.495c.673-1.167 2.357-1.167 3.03 0l6.28 10.875c.673 1.167-.17 2.625-1.516 2.625H3.72c-1.347 0-2.189-1.458-1.515-2.625L8.485 2.495zM10 5a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5A.75.75 0 0110 5zm0 9a1 1 0 100-2 1 1 0 000 2z"
                    clipRule="evenodd"
                  />
                </svg>
                <span>CDC Stream Prerequisites Missing</span>
              </div>
              <p className="mt-1.5 leading-relaxed text-amber-700">
                Your database connection is not configured for CDC. Accelerated Polling is activated as a fallback.
              </p>
              
              {/* Detailed DB steps */}
              <div className="mt-3 rounded border border-amber-200 bg-white/70 p-2.5 text-[11px] text-amber-800 space-y-1">
                <div className="font-semibold text-amber-900">Required Configuration:</div>
                {sourceType === "postgresql" ? (
                  <>
                    <div>1. Set <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">wal_level = logical</code> in postgresql.conf</div>
                    <div>2. Restart database server to apply parameter changes.</div>
                    <div>3. Ensure database user has <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">REPLICATION</code> attribute.</div>
                  </>
                ) : sourceType === "mysql" ? (
                  <>
                    <div>1. Enable binary logs with <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">log_bin = ON</code></div>
                    <div>2. Set <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">binlog_format = ROW</code></div>
                    <div>3. Ensure database user has replication privileges.</div>
                  </>
                ) : (
                  <>
                    <div>• For PostgreSQL: Set <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">wal_level = logical</code> and grant REPLICATION rights.</div>
                    <div>• For MySQL: Set <code className="font-mono bg-amber-100/80 px-1 rounded text-amber-900">log_bin = ON</code> and binlog format to ROW.</div>
                  </>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
