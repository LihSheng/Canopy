"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  createConnection,
  fetchConnectionTest,
  fetchTableDiscovery,
  createDataset,
  previewStaticFile,
  deleteStaticFilePreview,
  createProject,
} from "@/lib/api/data-source";
import type { DiscoveredTable, StaticFilePreview } from "@/lib/api/types";
import { SyncPolicyEditor, type SyncPolicy } from "@/components/data-studio/sync-policy-editor";
import { PreviewGrid } from "@/components/preview-grid";
import { ROUTES, ERROR_MESSAGES, UI_LABELS, FILE_ACCEPT } from "@/lib/constants";

type Step = 1 | 2 | 3;

const DEFAULT_POLICY: SyncPolicy = {
  syncMode: "batch",
  batchStrategy: "full_snapshot",
  cursorColumn: "",
  frequencyMinutes: 1440,
};

const isDbSource = (source: string): boolean => {
  return source === "postgresql" || source === "mysql";
}

export const SourceSetupWizard = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sourceType = searchParams.get("source") ?? "static_file";
  const isDb = isDbSource(sourceType);

  const [step, setStep] = useState<Step>(1);

  // --- Shared state ---
  const [error, setError] = useState<string | null>(null);

  // --- DB connection form (Step 1) ---
  const [host, setHost] = useState("");
  const [port, setPort] = useState(isDb && sourceType === "mysql" ? "3306" : "5432");
  const [database, setDatabase] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [connectionName, setConnectionName] = useState("");
  const [testing, setTesting] = useState(false);
  const [testSuccess, setTestSuccess] = useState(false);
  const [supportsCdc, setSupportsCdc] = useState(false);
  const [connectionId, setConnectionId] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);

  // --- Static file upload (Step 1) ---
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [preview, setPreview] = useState<StaticFilePreview | null>(null);
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());
  const [activeSheetName, setActiveSheetName] = useState<string>("");

  // --- DB table discovery & selection (Step 2) ---
  const [tables, setTables] = useState<DiscoveredTable[]>([]);
  const [loadingTables, setLoadingTables] = useState(false);
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());

  // --- Sync policy (Step 3) ---
  const [tablePolicies, setTablePolicies] = useState<Record<string, SyncPolicy>>({});
  const [deploying, setDeploying] = useState(false);

  // ---- Step 1 handlers ----

  const handleTestConnection = useCallback(async () => {
    setTesting(true);
    setError(null);
    try {
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

      const result = await fetchConnectionTest(conn.id);
      if (result.success) {
        setTestSuccess(true);
        setSupportsCdc(result.supports_cdc ?? false);
      } else {
        setError(result.message ?? ERROR_MESSAGES.connectionTestFailed);
        setSupportsCdc(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : ERROR_MESSAGES.connectionFailed);
      setSupportsCdc(false);
    } finally {
      setTesting(false);
    }
  }, [projectId, sourceType, connectionName, host, port, database, username, password]);

  const handleDbNext = useCallback(async () => {
    if (!connectionId) return;
    setLoadingTables(true);
    setError(null);
    try {
      const discovered = await fetchTableDiscovery(connectionId);
      setTables(discovered);
      setStep(2);
    } catch {
      setError(ERROR_MESSAGES.failedToDiscoverTables);
    } finally {
      setLoadingTables(false);
    }
  }, [connectionId]);

  const handleFileDrop = useCallback(async (dropped: File) => {
    setFile(dropped);
    setError(null);
    setPreparing(true);
    try {
      const result = await previewStaticFile(dropped, sourceType);
      setPreview(result);
      const sheetNames = result.sheet_profiles.map((s) => s.sheet_name);
      setSelectedSheets(new Set(sheetNames));
      setActiveSheetName(sheetNames[0] || "");
      setStep(2); // Auto advance to Step 2 after upload
    } catch (err) {
      setError(err instanceof Error ? err.message : ERROR_MESSAGES.uploadFailed);
    } finally {
      setPreparing(false);
    }
  }, [sourceType]);

  const handleFileReset = useCallback(async () => {
    const sourceFilePath = preview?.source_file_path;
    if (sourceFilePath) {
      await deleteStaticFilePreview(sourceFilePath).catch(() => undefined);
    }
    setFile(null);
    setPreview(null);
    setSelectedSheets(new Set());
    setActiveSheetName("");
    setError(null);
    setPreparing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [preview]);

  // ---- Step 2 handlers ----

  // DB table toggling
  const toggleTable = useCallback((tableName: string) => {
    setSelectedTables((prev) => {
      const next = new Set(prev);
      if (next.has(tableName)) next.delete(tableName);
      else next.add(tableName);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    if (isDb) {
      if (selectedTables.size === tables.length) {
        setSelectedTables(new Set());
      } else {
        setSelectedTables(new Set(tables.map((t) => t.table_name)));
      }
    } else if (preview) {
      if (selectedSheets.size === preview.sheet_profiles.length) {
        setSelectedSheets(new Set());
      } else {
        setSelectedSheets(new Set(preview.sheet_profiles.map((s) => s.sheet_name)));
      }
    }
  }, [isDb, tables, selectedTables, preview, selectedSheets]);

  // Sheet toggling for static files
  const toggleSheet = useCallback((name: string) => {
    setSelectedSheets((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      if (activeSheetName === name && !next.has(name)) {
        setActiveSheetName(next.values().next().value || "");
      }
      return next;
    });
  }, [activeSheetName]);

  const handleStep2Next = useCallback(() => {
    if (isDb) {
      const policies: Record<string, SyncPolicy> = {};
      for (const name of selectedTables) {
        const table = tables.find((t) => t.table_name === name);
        policies[name] = {
          ...DEFAULT_POLICY,
          cursorColumn: table?.detected_cursor_column ?? "",
        };
      }
      setTablePolicies(policies);
    } else {
      // For static files, create a basic default policy per selected sheet
      const policies: Record<string, SyncPolicy> = {};
      for (const name of selectedSheets) {
        policies[name] = { ...DEFAULT_POLICY };
      }
      setTablePolicies(policies);
    }
    setStep(3);
  }, [isDb, selectedTables, tables, selectedSheets]);

  // ---- Step 3 handlers ----

  const _updatePolicy = useCallback(
    (tableName: string, policy: SyncPolicy) => {
      setTablePolicies((prev) => ({ ...prev, [tableName]: policy }));
    },
    [],
  );

  const handleFinish = useCallback(async () => {
    if (!connectionId && !preview) return;
    setDeploying(true);
    setError(null);
    try {
      if (isDb && connectionId && projectId) {
        // Deploy DB datasets
        const results = await Promise.all(
          Array.from(selectedTables).map((tableName) => {
            const policy = tablePolicies[tableName] ?? DEFAULT_POLICY;
            return createDataset({
              project_id: projectId,
              connection_id: connectionId,
              name: tableName,
              source_object_name: tableName,
              sync_mode: policy.syncMode,
              batch_strategy:
                policy.syncMode === "batch" ? policy.batchStrategy : null,
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
          router.push(ROUTES.connections.datasets);
        }
      } else if (preview && file) {
        // Create connection from static file preview
        let pid = projectId;
        if (!pid) {
          const project = await createProject({ name: "Default Project" });
          pid = project.id;
        }
        const conn = await createConnection({
          project_id: pid,
          source_type: "static_file",
          name: file.name || preview.file_name || "Static File",
          config_json: {
            file_name: preview.file_name,
            source_file_path: preview.source_file_path,
          },
        });
        // Create datasets for selected sheets
        const selected = preview.sheet_profiles.filter((s) => selectedSheets.has(s.sheet_name));
        for (const sheet of selected) {
          await createDataset({
            project_id: pid,
            connection_id: conn.id,
            name: sheet.sheet_name,
            source_object_name: sheet.sheet_name,
            sync_mode: "batch",
            batch_strategy: "full_snapshot",
          });
        }
        router.push(ROUTES.connections.datasets);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : ERROR_MESSAGES.failedToCreateDatasets);
    } finally {
      setDeploying(false);
    }
  }, [connectionId, projectId, isDb, preview, file, selectedTables, selectedSheets, tablePolicies, router, supportsCdc]);

  // ---- Derived state ----

  const selectedCount = isDb ? selectedTables.size : selectedSheets.size;
  const totalCount = isDb ? tables.length : preview?.sheet_profiles.length ?? 0;
  const canProceedToStep2 = isDb ? (testSuccess && connectionId != null) : (preview != null);
  const _canProceedToStep3 = selectedCount > 0;
  const maxStep: Step = isDb ? 3 : 2;
  const stepLabel = (s: Step) =>
    s === 1 ? (isDb ? "Authenticate" : "Upload") : s === 2 ? "Select Objects" : "Sync Policy";

  // ---- Active sheet for preview (static files) ----
  const activeSheet = preview?.sheet_profiles.find((s) => s.sheet_name === activeSheetName) ?? null;

  // ---- Active table for preview (DB) ----
  const activeTableName = isDb && tables.length > 0
    ? (Array.from(selectedTables)[0] || tables[0]?.table_name)
    : null;
  const activeTable = activeTableName ? tables.find((t) => t.table_name === activeTableName) ?? null : null;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2 text-sm">
        {([1, 2, 3] as const).filter((s) => s <= maxStep).map((s) => (
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
              {stepLabel(s)}
            </span>
            {s < maxStep && <span className="text-zinc-300">→</span>}
          </div>
        ))}
      </div>

      {/* --- Step 1: Authenticate / Upload --- */}
      {step === 1 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          {isDb ? (
            <>
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Connect Database</h3>

              <div className="mb-4">
                <label className="block text-xs font-medium text-zinc-500">Source type</label>
                <input
                  value={sourceType === "postgresql" ? "PostgreSQL" : "MySQL"}
                  disabled
                  className="mt-1 w-full rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 text-sm text-zinc-500"
                />
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
                    placeholder={sourceType === "mysql" ? "3306" : "5432"}
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

              {error && (
                <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {error}
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
                  onClick={() => router.push(ROUTES.connections.sources)}
                  className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
                >
                  Back to Sources
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
                    onClick={handleDbNext}
                    disabled={!canProceedToStep2 || loadingTables}
                    className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {loadingTables ? UI_LABELS.loading : UI_LABELS.next}
                  </button>
                </div>
              </div>
            </>
          ) : (
            <>
              <h3 className="mb-4 text-lg font-semibold text-zinc-900">Upload File</h3>

              <input
                ref={fileInputRef}
                type="file"
                data-testid="file-input"
                className="hidden"
                accept={FILE_ACCEPT}
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) {
                    void handleFileDrop(f);
                    e.currentTarget.value = "";
                  }
                }}
              />

              {preparing ? (
                <div className="flex items-center justify-center py-12">
                  <div className="text-sm text-zinc-500">Processing file...</div>
                </div>
              ) : !preview ? (
                <div
                  role="button"
                  tabIndex={0}
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files[0];
                    if (f) void handleFileDrop(f);
                  }}
                  onClick={() => fileInputRef.current?.click()}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      fileInputRef.current?.click();
                    }
                  }}
                  className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-zinc-300 bg-zinc-50 p-12 transition-colors hover:border-zinc-400 hover:bg-zinc-100"
                >
                  <svg
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    className="mb-3 h-10 w-10 text-zinc-400"
                  >
                    <path d="M9.25 13.25a.75.75 0 001.5 0V4.636l2.955 3.129a.75.75 0 001.09-1.03l-4.25-4.5a.75.75 0 00-1.09 0l-4.25 4.5a.75.75 0 101.09 1.03L9.25 4.636V13.25z" />
                    <path d="M3.5 12.75a.75.75 0 00-1.5 0v2.5A2.75 2.75 0 004.75 18h10.5A2.75 2.75 0 0018 15.25v-2.5a.75.75 0 00-1.5 0v2.5c0 .69-.56 1.25-1.25 1.25H4.75c-.69 0-1.25-.56-1.25-1.25v-2.5z" />
                  </svg>
                  <p className="text-sm font-medium text-zinc-700">
                    Drop your file here, or{" "}
                    <span className="text-indigo-600">browse</span>
                  </p>
                  <p className="mt-1 text-xs text-zinc-400">
                    Excel (.xlsx) or CSV files
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border border-zinc-200 bg-zinc-50 p-4">
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{file?.name ?? preview.file_name}</p>
                      <p className="text-xs text-zinc-500">
                        {preview.sheet_profiles.length} sheet{preview.sheet_profiles.length !== 1 ? "s" : ""} detected
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleFileReset()}
                      className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50"
                    >
                      Remove file
                    </button>
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => setStep(2)}
                      className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
                    >
                      {UI_LABELS.next}
                    </button>
                  </div>
                </div>
              )}

              {error && (
                <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                  {error}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* --- Step 2: Select Objects --- */}
      {step === 2 && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-zinc-900">
            {isDb ? "Select Tables" : "Select Sheets"}
          </h3>

          <div className="flex flex-col gap-4 lg:flex-row">
            {/* Left: object list */}
            <div className="min-w-0 flex-1">
              <div className="mb-4 flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-zinc-700">
                  <input
                    type="checkbox"
                    checked={selectedCount === totalCount && totalCount > 0}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded border-zinc-300"
                  />
                    {UI_LABELS.selectAll}
                  </label>
                <span className="text-xs text-zinc-400">
                  {selectedCount} of {totalCount} selected
                </span>
              </div>

              <ul className="max-h-80 space-y-1 overflow-y-auto">
                {isDb ? (
                  tables.map((table) => (
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
                                {" "}&middot; cursor:{" "}
                                <span className="text-emerald-600">{table.detected_cursor_column}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </label>
                    </li>
                  ))
                ) : (
                  preview?.sheet_profiles.map((sheet) => (
                    <li key={sheet.sheet_name}>
                      <label className="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 transition-colors hover:bg-zinc-50">
                        <input
                          type="checkbox"
                          checked={selectedSheets.has(sheet.sheet_name)}
                          onChange={() => toggleSheet(sheet.sheet_name)}
                          className="h-4 w-4 rounded border-zinc-300"
                        />
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium text-zinc-900">{sheet.sheet_name}</div>
                          <div className="text-xs text-zinc-500">
                            {sheet.data_row_count} data rows, {sheet.column_count} columns
                          </div>
                        </div>
                      </label>
                    </li>
                  ))
                )}
              </ul>
            </div>

            {/* Right: preview pane */}
            {isDb && activeTable && (
              <div className="w-full lg:w-96">
                <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
                  <h4 className="mb-2 text-xs font-semibold text-zinc-500 uppercase">
                    Preview: {activeTable.table_name}
                  </h4>
                  <div className="max-h-60 overflow-auto">
                    {activeTable.columns.length > 0 ? (
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-zinc-200 text-left">
                            <th className="px-2 py-1 font-medium text-zinc-500">Column</th>
                            <th className="px-2 py-1 font-medium text-zinc-500">Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {activeTable.columns.slice(0, 10).map((col, i) => (
                            <tr key={i} className="border-b border-zinc-100">
                              <td className="px-2 py-1 text-zinc-900">{col.name}</td>
                              <td className="px-2 py-1 text-zinc-500">{col.data_type}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    ) : (
                      <p className="text-xs text-zinc-400">No columns</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {!isDb && activeSheet && (
              <div className="w-full lg:w-96">
                <div className="rounded-lg border border-zinc-100 bg-zinc-50 p-3">
                  <h4 className="mb-2 text-xs font-semibold text-zinc-500 uppercase">
                    Preview: {activeSheet.sheet_name}
                  </h4>
                  <PreviewGrid
                    columns={activeSheet.preview_columns}
                    rows={activeSheet.preview_rows}
                    totalRowCount={activeSheet.data_row_count}
                  />
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-6 flex justify-between">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
            >
              {UI_LABELS.back}
            </button>
            {isDb ? (
              <button
                type="button"
                onClick={() => handleStep2Next()}
                disabled={selectedCount === 0}
                className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {UI_LABELS.next} ({selectedCount})
              </button>
            ) : (
              <button
                type="button"
                onClick={() => void handleFinish()}
                disabled={deploying || selectedCount === 0}
                className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {deploying ? UI_LABELS.deploying : UI_LABELS.finishAndDeploy}
              </button>
            )}
          </div>
        </div>
      )}

      {/* --- Step 3: Configure Sync Policy --- */}
      {step === 3 && isDb && (
        <div className="rounded-lg border border-zinc-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-zinc-900">Configure Sync Policy</h3>
          <p className="mb-4 text-sm text-zinc-500">
            Choose how each selected object should be synchronized.
          </p>

          <div className="space-y-4">
            {isDb ? (
              Array.from(selectedTables).map((tableName) => {
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
                    onChange={(p) => _updatePolicy(tableName, p)}
                  />
                );
              })
            ) : (
              Array.from(selectedSheets).map((sheetName) => {
                const policy = tablePolicies[sheetName] ?? DEFAULT_POLICY;
                return (
                  <SyncPolicyEditor
                    key={sheetName}
                    tableName={sheetName}
                    schemaColumns={[]}
                    detectedCursorColumn={null}
                    supportsCdc={false}
                    sourceType="static_file"
                    value={policy}
                    onChange={(p) => _updatePolicy(sheetName, p)}
                  />
                );
              })
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {error}
            </div>
          )}

          <div className="mt-6 rounded-lg bg-zinc-50 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-500">
                {selectedCount} object{selectedCount !== 1 ? "s" : ""} configured
              </span>
              <span className="text-zinc-400">
                {isDb
                  ? Array.from(selectedTables).map((name) => {
                      const p = tablePolicies[name];
                      return `${name} (${p?.syncMode ?? "batch"})`;
                    }).join(", ")
                  : Array.from(selectedSheets).map((name) => {
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
              onClick={() => void handleFinish()}
              disabled={deploying}
              className="rounded-md border border-zinc-900 bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {deploying ? UI_LABELS.deploying : UI_LABELS.finishAndDeploy}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
