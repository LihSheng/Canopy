"use client";

import { useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  createConnection,
  fetchConnectionTest,
  fetchTableDiscovery,
  createDataset,
} from "@/lib/api/data-source";
import type { DiscoveredTable } from "@/lib/api/types";
import { SyncPolicyEditor, type SyncPolicy } from "@/components/data-studio/sync-policy-editor";
import { ROUTES, ERROR_MESSAGES, UI_LABELS, QUERY_PARAMS } from "@/lib/constants";

type Step = 1 | 2 | 3;

const DEFAULT_POLICY: SyncPolicy = {
  syncMode: "batch",
  batchStrategy: "full_snapshot",
  cursorColumn: "",
  frequencyMinutes: 1440,
};

type ProgressStage = {
  title: string;
  description: string;
  stepLabel: string;
};

const progressDotClass = (active: boolean): string =>
  `flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
    active ? "bg-zinc-900 text-white" : "bg-zinc-100 text-zinc-400"
  }`;

const progressTextClass = (active: boolean): string =>
  active ? "font-medium text-zinc-900" : "text-zinc-400";

export const ConnectionWizard = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialSource = searchParams.get(QUERY_PARAMS.source) ?? "postgresql";
  const [step, setStep] = useState<Step>(1);

  // Step 1: Authenticate
  const [sourceType, setSourceType] = useState(initialSource);
  const [host, setHost] = useState("");
  const [port, setPort] = useState("5432");
  const [database, setDatabase] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [connectionName, setConnectionName] = useState("");
  const [testing, setTesting] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);
  const [testSuccess, setTestSuccess] = useState(false);
  const [supportsCdc, setSupportsCdc] = useState(false);
  const [connectionId, setConnectionId] = useState<string | null>(null);

  // Step 2: Select Objects
  const [tables, setTables] = useState<DiscoveredTable[]>([]);
  const [loadingTables, setLoadingTables] = useState(false);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());

  // Step 3: Configure Sync Policy
  const [tablePolicies, setTablePolicies] = useState<Record<string, SyncPolicy>>({});
  const [deploying, setDeploying] = useState(false);
  const [deployError, setDeployError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  const handleSourceTypeChange = useCallback(
    (value: string) => {
      setSourceType(value);
      setStep(1);
      setTestSuccess(false);
      setTestError(null);
      setSupportsCdc(false);
      setConnectionId(null);
      setTables([]);
      setSelectedTables(new Set());
      setTablePolicies({});
      setDeployError(null);
    },
    [],
  );

  // --- Step 1 handlers ---

  const handleTestConnection = useCallback(async () => {
    setTesting(true);
    setTestError(null);
    try {
      // Create the connection first
      const conn = await createConnection({
        project_id: projectId ?? "default",
        source_type: sourceType,
        name: connectionName || `${sourceType} - ${host}:${port}/${database}`,
        config_json: {
          host,
          port: Number(port),
          database,
          username,
          password,
        },
      });
      setConnectionId(conn.id);
      if (!projectId) setProjectId(conn.project_id);

      // Test the connection
      const result = await fetchConnectionTest(conn.id);
      if (result.success) {
        setTestSuccess(true);
        setSupportsCdc(result.supports_cdc ?? false);
      } else {
        setTestError(result.message ?? ERROR_MESSAGES.connectionTestFailed);
        setSupportsCdc(false);
      }
    } catch (err) {
      setTestError(err instanceof Error ? err.message : ERROR_MESSAGES.connectionFailed);
      setSupportsCdc(false);
    } finally {
      setTesting(false);
    }
  }, [projectId, sourceType, connectionName, host, port, database, username, password]);

  const handleNextToStep2 = useCallback(async () => {
    if (!connectionId) return;
    setLoadingTables(true);
    try {
      const discovered = await fetchTableDiscovery(connectionId);
      setTables(discovered);
      setStep(2);
    } catch {
      setTestError(ERROR_MESSAGES.failedToDiscoverTables);
    } finally {
      setLoadingTables(false);
    }
  }, [connectionId]);

  // --- Step 2 handlers ---

  const toggleTable = useCallback((tableName: string) => {
    setSelectedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) {
        next.delete(tableName);
      } else {
        next.add(tableName);
      }
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (selectedTables.size === tables.length) {
      setSelectedTables(new Set());
    } else {
      setSelectedTables(new Set(tables.map((t) => t.table_name)));
    }
  }, [tables, selectedTables]);

  const handleNextToStep3 = useCallback(() => {
    const policies: Record<string, SyncPolicy> = {};
    for (const name of selectedTables) {
      const table = tables.find((t) => t.table_name === name);
      policies[name] = {
        ...DEFAULT_POLICY,
        cursorColumn: table?.detected_cursor_column ?? "",
      };
    }
    setTablePolicies(policies);
    setStep(3);
  }, [selectedTables, tables]);

  // --- Step 3 handlers ---

  const updatePolicy = useCallback(
    (tableName: string, policy: SyncPolicy) => {
      setTablePolicies((prev) => ({ ...prev, [tableName]: policy }));
    },
    [],
  );

  const handleFinish = useCallback(async () => {
    if (!connectionId || !projectId) return;
    setDeploying(true);
    setDeployError(null);
    try {
      const results = await Promise.all(
        Array.from(selectedTables).map((tableName) => {
          const policy = tablePolicies[tableName] ?? DEFAULT_POLICY;
          return createDataset({
            project_id: projectId,
            connection_id: connectionId,
            name: tableName,
            source_object_name: tableName,
            sync_mode: policy.syncMode,
            batch_strategy: policy.syncMode === "batch" ? policy.batchStrategy : null,
            real_time_strategy:
              policy.syncMode === "real_time"
                ? (policy.realTimeStrategy ?? (supportsCdc ? "cdc" : "polling"))
                : null,
            cursor_column:
              policy.syncMode === "batch" && policy.batchStrategy === "incremental_cursor"
                ? policy.cursorColumn
                : null,
          });
        }),
      );
      if (results.length > 0) {
        router.push(ROUTES.connections.home);
      }
    } catch (err) {
      setDeployError(err instanceof Error ? err.message : ERROR_MESSAGES.failedToCreateDatasets);
    } finally {
      setDeploying(false);
    }
  }, [connectionId, projectId, selectedTables, tablePolicies, router, supportsCdc]);

  const selectedCount = selectedTables.size;
  const canProceedToStep2 = testSuccess && connectionId != null;
  const canProceedToStep3 = selectedCount > 0;
  const busyStage: ProgressStage | null = testing
    ? {
        title: "Initiating connection...",
        description: "Verifying credentials and creating the connection record.",
        stepLabel: "Authenticate",
      }
    : loadingTables
      ? {
          title: "Loading tables...",
          description: "Discovering table names, row counts, and schemas.",
          stepLabel: "Select Objects",
        }
      : deploying
        ? {
            title: "Preparing datasets...",
            description: "Saving sync policies and creating datasets.",
            stepLabel: "Sync Policy",
          }
        : null;
  const busyStages: ProgressStage[] = [
    {
      title: "Initiating connection...",
      description: "Verifying credentials and creating the connection record.",
      stepLabel: "Authenticate",
    },
    {
      title: "Loading tables...",
      description: "Discovering table names, row counts, and schemas.",
      stepLabel: "Select Objects",
    },
    {
      title: "Preparing datasets...",
      description: "Saving sync policies and creating datasets.",
      stepLabel: "Sync Policy",
    },
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm">
        {([1, 2, 3] as const).map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                step === s
                  ? "bg-zinc-900 text-white"
                  : step > s
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-zinc-100 text-zinc-400"
              }`}
            >
              {step > s ? "✓" : s}
            </div>
            <span className={step === s ? "font-medium text-zinc-900" : "text-zinc-400"}>
              {s === 1 ? "Authenticate" : s === 2 ? "Select Objects" : "Sync Policy"}
            </span>
            {s < 3 && <span className="text-zinc-300">→</span>}
          </div>
        ))}
      </div>

      {/* --- Step 1: Authenticate --- */}
      {step === 1 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          {busyStage ? (
            <div className="flex min-h-[280px] flex-col items-center justify-center gap-5 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-200 bg-zinc-50">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900" />
              </div>
              <div>
                <p className="text-base font-semibold text-zinc-900">{busyStage.title}</p>
                <p className="mt-1 text-sm text-zinc-500">{busyStage.description}</p>
              </div>
              <div className="w-full max-w-md space-y-3 rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-left">
                {busyStages.map((stage, index) => {
                  const active = stage.stepLabel === busyStage.stepLabel;
                  const completed = busyStages.findIndex((item) => item.stepLabel === busyStage.stepLabel) > index;
                  return (
                    <div key={stage.stepLabel} className="flex items-start gap-3">
                      <div className={progressDotClass(active || completed)}>
                        {completed ? "✓" : index + 1}
                      </div>
                      <div className="min-w-0">
                        <p className={`text-sm ${progressTextClass(active || completed)}`}>{stage.title}</p>
                        <p className="text-xs text-zinc-500">{stage.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <>
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Connect Database</h3>

              <div className="mb-4">
                <label className="block text-xs font-medium text-zinc-500">Source type</label>
                <select
                  value={sourceType}
                  onChange={(e) => handleSourceTypeChange(e.target.value)}
                  className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 focus:border-zinc-400 focus:outline-none"
                >
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Host</label>
                  <input
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="localhost"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Port</label>
                  <input
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    placeholder="5432"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Database</label>
                  <input
                    value={database}
                    onChange={(e) => setDatabase(e.target.value)}
                    placeholder="mydb"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Username</label>
                  <input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="user"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Password</label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-500">Connection name</label>
                  <input
                    value={connectionName}
                    onChange={(e) => setConnectionName(e.target.value)}
                    placeholder="Optional"
                    className="mt-1 w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-700 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
                  />
                </div>
              </div>

              {testError && (
                <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {testError}
                </div>
              )}

              {testSuccess && (
                <div className="mt-4 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                  Connection successful
                </div>
              )}

              <div className="mt-6 flex justify-between">
                <button
                  type="button"
                  onClick={() => router.push(ROUTES.connections.home)}
                  className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
                >
                  {UI_LABELS.cancel}
                </button>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleTestConnection}
                    disabled={testing || !host || !database}
                    className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {testing ? UI_LABELS.testing : UI_LABELS.testConnection}
                  </button>
                  <button
                    type="button"
                    onClick={handleNextToStep2}
                    disabled={!canProceedToStep2 || loadingTables}
                    className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loadingTables ? UI_LABELS.loading : UI_LABELS.next}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* --- Step 2: Select Objects --- */}
      {step === 2 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-zinc-900">Select Tables</h3>

          <div className="mb-4 flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-zinc-700">
              <input
                type="checkbox"
                checked={selectedCount === tables.length && tables.length > 0}
                onChange={toggleSelectAll}
                className="h-4 w-4 rounded border-zinc-300"
              />
              {UI_LABELS.selectAll}
            </label>
            <span className="text-xs text-zinc-400">
              {selectedCount} of {tables.length} selected
            </span>
          </div>

          <ul className="space-y-1">
            {tables.map((table) => (
              <li key={table.table_name}>
                <label className="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 transition-colors hover:bg-zinc-50">
                  <input
                    type="checkbox"
                    checked={selectedTables.has(table.table_name)}
                    onChange={() => toggleTable(table.table_name)}
                    className="h-4 w-4 rounded border-zinc-300"
                  />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-medium text-zinc-900">{table.table_name}</div>
                    <div className="text-xs text-zinc-400">
                      ~{table.row_count_estimate.toLocaleString()} rows
                      &middot; {table.columns.length} columns
                      {table.detected_cursor_column && (
                        <>
                          {" "}
                          &middot; cursor:{" "}
                          <span className="text-emerald-600">{table.detected_cursor_column}</span>
                        </>
                      )}
                    </div>
                  </div>
                </label>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex justify-between">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
            >
              {UI_LABELS.back}
            </button>
            <button
              type="button"
              onClick={handleNextToStep3}
              disabled={!canProceedToStep3}
              className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {UI_LABELS.next} ({selectedCount})
            </button>
          </div>
        </div>
      )}

      {/* --- Step 3: Configure Sync Policy --- */}
      {step === 3 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          {deploying ? (
            <div className="flex min-h-[280px] flex-col items-center justify-center gap-5 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full border border-zinc-200 bg-zinc-50">
                <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-zinc-900" />
              </div>
              <div>
                <p className="text-base font-semibold text-zinc-900">Preparing datasets...</p>
                <p className="mt-1 text-sm text-zinc-500">Saving sync policies and creating datasets.</p>
              </div>
              <div className="text-xs text-zinc-400">Do not close this page while deployment is running.</div>
            </div>
          ) : (
            <>
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Configure Sync Policy</h3>
              <p className="mb-4 text-sm text-zinc-500">
                Choose how each selected table should be synchronized.
              </p>

              <div className="space-y-4">
                {Array.from(selectedTables).map((tableName) => {
                  const table = tables.find((t) => t.table_name === tableName);
                  const policy = tablePolicies[tableName] ?? DEFAULT_POLICY;
                  return (
                    <SyncPolicyEditor
                      key={tableName}
                      tableName={tableName}
                      schemaColumns={table?.columns ?? []}
                      detectedCursorColumn={table?.detected_cursor_column ?? null}
                      supportsCdc={supportsCdc}
                      sourceType={sourceType}
                      value={policy}
                      onChange={(p) => updatePolicy(tableName, p)}
                    />
                  );
                })}
              </div>

              {deployError && (
                <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {deployError}
                </div>
              )}

              <div className="mt-6 rounded-lg bg-zinc-50 p-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-zinc-500">
                    {selectedCount} table{selectedCount !== 1 ? "s" : ""} configured
                  </span>
                  <span className="text-zinc-400">
                    {Array.from(selectedTables).map((name) => {
                      const p = tablePolicies[name];
                      return `${name} (${p?.syncMode ?? "batch"})`;
                    }).join(", ")}
                  </span>
                </div>
              </div>

              <div className="mt-6 flex justify-between">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
                >
                  {UI_LABELS.back}
                </button>
                <button
                  type="button"
                  onClick={handleFinish}
                  disabled={deploying}
                  className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {deploying ? UI_LABELS.deploying : UI_LABELS.finishAndDeploy}
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
