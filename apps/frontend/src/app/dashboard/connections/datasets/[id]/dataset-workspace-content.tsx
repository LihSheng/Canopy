"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import {
  fetchDataset,
  fetchDatasetDeleteSummary,
  fetchDatasetPreview,
  fetchDatasetVersions,
  fetchDatasetHealth,
  fetchDatasetLineage,
  deleteDataset,
  deleteDatasetVersion,
  fetchRuns,
  reimportDatasetVersion,
  refreshDatasetVersion,
  previewStaticFile,
  updateSyncPolicy,
  updateDataset,
  fetchConnection,
} from "@/lib/api/data-source";
import type {
  Dataset,
  DatasetVersion,
  DatasetHealth,
  Run,
  DatasetDeleteSummary,
  Connection,
} from "@/lib/api/types";
import type { DatasetPreviewResponse } from "@/lib/api/data-source";
import { DatasetPreviewGrid } from "@/components/dataset-preview-grid";
import { DatasetSummaryCards } from "@/components/dataset-summary-cards";
import { DatasetCharts } from "@/components/dataset-charts";
import { VersionHistory } from "@/components/version-history";
import { HealthPanel } from "@/components/health-panel";
import { RunHistory } from "@/components/run-history";
import { LineageView } from "@/components/lineage-view";
import {
  ConfirmDialog,
  ErrorState,
  LoadingSpinner,
  NoticeBanner,
  useToast,
} from "@/components/shared";
import { SyncPolicyEditor, type SyncPolicy } from "@/components/data-studio/sync-policy-editor";
import { EntityTab } from "@/components/entity-mapping/entity-tab";
import { ROUTES, ERROR_MESSAGES, UI_LABELS, FILE_ACCEPT, DATASET_STATUS_COLORS, errorMessageFailedToLoad } from "@/lib/constants";

const TABS = [
  "Overview",
  "Preview",
  "Schema",
  "Transform",
  "Lineage",
  "Runs",
  "Versions",
  "Details",
  "Entity",
] as const;

type Tab = (typeof TABS)[number];

type Props = {
  datasetId: string;
};

const DatasetWorkspaceContent = ({ datasetId }: Props) => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeTab = (searchParams.get("tab") as Tab) || "Overview";
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [connection, setConnection] = useState<Connection | null>(null);
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [previewPage, setPreviewPage] = useState(1);
  const previewPageSize = 25;
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [health, setHealth] = useState<DatasetHealth | null>(null);
  const [deleteSummary, setDeleteSummary] = useState<DatasetDeleteSummary | null>(null);
  const [lineage, setLineage] = useState<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] } | null>(null);
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [deletingDataset, setDeletingDataset] = useState(false);
  const [deletingVersionId, setDeletingVersionId] = useState<string | null>(null);
  const [deleteDialogKind, setDeleteDialogKind] = useState<"dataset" | "version" | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<DatasetVersion | null>(null);
  const [refreshingLatest, setRefreshingLatest] = useState(false);
  const [editingSyncPolicy, setEditingSyncPolicy] = useState(false);
  const [savingSyncPolicy, setSavingSyncPolicy] = useState(false);
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState("");
  const [savingName, setSavingName] = useState(false);
  const editNameRef = useRef<HTMLInputElement | null>(null);
  const toast = useToast();
  const supportsCdc = !!connection?.config_json?.supports_cdc;
  const realTimeStrategyValue: SyncPolicy["realTimeStrategy"] =
    dataset?.real_time_strategy === "cdc" || dataset?.real_time_strategy === "polling"
      ? dataset.real_time_strategy
      : supportsCdc
        ? "cdc"
        : "polling";

  const handleFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";

    setRefreshingLatest(true);
    setActionError(null);
    try {
      const staticPreview = await previewStaticFile(file, "static_file");
      const firstSheet =
        staticPreview.sheet_profiles.find((sheet) => sheet.data_row_count > 0) ??
        staticPreview.sheet_profiles[0];
      if (!firstSheet) {
        throw new Error("No sheets found in the file");
      }
      const newVersion = await reimportDatasetVersion(
        datasetId,
        staticPreview.source_file_path,
        firstSheet.preview_columns,
        firstSheet.sheet_name,
      );
      toast.success(
        "Latest data refreshed",
        `v${newVersion.version_number} is now active.`,
      );
      await load();
      await loadPreview();
    } catch (err) {
      const message = err instanceof Error ? err.message : ERROR_MESSAGES.uploadFailed;
      setActionError(message);
      toast.danger("Refresh failed", message);
    } finally {
      setRefreshingLatest(false);
    }
  };

  const handleRefreshLatest = async () => {
    if (connection?.source_type === "static_file") {
      fileInputRef.current?.click();
      return;
    }

    setRefreshingLatest(true);
    setActionError(null);
    try {
      const newVersion = await refreshDatasetVersion(datasetId);
      toast.success(
        "Latest data refreshed",
        `v${newVersion.version_number} is now active.`,
      );
      await load();
      await loadPreview();
    } catch (err) {
      const message = err instanceof Error ? err.message : ERROR_MESSAGES.failedToRefreshDataset;
      setActionError(message);
      toast.danger("Refresh failed", message);
    } finally {
      setRefreshingLatest(false);
    }
  };

  const handleSaveSyncPolicy = async (policy: SyncPolicy) => {
    setSavingSyncPolicy(true);
    try {
      await updateSyncPolicy(datasetId, {
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
        frequency_minutes: policy.frequencyMinutes,
      });
      await load();
      setEditingSyncPolicy(false);
      toast.success("Sync policy updated", "Dataset sync configuration saved.");
    } catch (err) {
      const message = err instanceof Error ? err.message : ERROR_MESSAGES.failedToSaveSyncPolicy;
      setActionError(message);
      toast.danger("Save failed", message);
    } finally {
      setSavingSyncPolicy(false);
    }
  };

  const isValidDatasetName = (name: string): string | null => {
    const trimmed = name.trim();
    if (!trimmed) return "Dataset name must not be empty";
    if (!/^[A-Za-z]/.test(trimmed)) return "Dataset name must start with a letter";
    if (!/^[A-Za-z][A-Za-z0-9 _-]*$/.test(trimmed)) {
      return "Only letters, digits, spaces, hyphens, and underscores are allowed";
    }
    return null;
  };

  const handleStartEditName = () => {
    setEditNameValue(dataset?.name ?? "");
    setEditingName(true);
    // Focus the input on next tick after render
    requestAnimationFrame(() => editNameRef.current?.focus());
  };

  const handleCancelEditName = () => {
    setEditingName(false);
    setEditNameValue("");
    setActionError(null);
  };

  const handleSaveName = async () => {
    const validationError = isValidDatasetName(editNameValue);
    if (validationError) {
      setActionError(validationError);
      return;
    }

    const newName = editNameValue.trim();
    if (newName === dataset?.name) {
      setEditingName(false);
      return;
    }

    setSavingName(true);
    setActionError(null);
    try {
      await updateDataset(datasetId, { name: newName });
      setEditingName(false);
      toast.success("Dataset renamed", `Renamed to "${newName}".`);
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to rename dataset";
      setActionError(message);
      toast.danger("Rename failed", message);
    } finally {
      setSavingName(false);
    }
  };

  const handleNameKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveName();
    } else if (e.key === "Escape") {
      handleCancelEditName();
    }
  };

  const activeVersion = versions.find((v) => v.id === dataset?.active_version_id);
  const activeVersionNumber = activeVersion?.version_number;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const ds = await fetchDataset(datasetId);
      setDataset(ds);
      const [versionsData, healthData, lineageData, runsData, deleteSummaryData, connData] =
        await Promise.all([
          fetchDatasetVersions(datasetId),
          fetchDatasetHealth(datasetId),
          fetchDatasetLineage(datasetId),
          fetchRuns(datasetId),
          fetchDatasetDeleteSummary(datasetId),
          fetchConnection(ds.connection_id),
        ]);
      setVersions(versionsData);
      setHealth(healthData);
      setLineage(lineageData);
      setRuns(runsData);
      setDeleteSummary(deleteSummaryData);
      setConnection(connData);
    } catch (err) {
      setError(err instanceof Error ? err.message : errorMessageFailedToLoad("dataset"));
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const loadPreview = useCallback(async () => {
    setPreviewLoading(true);
    setPreviewError(null);
    try {
      const previewData = await fetchDatasetPreview(datasetId, {
        page: previewPage,
        page_size: previewPageSize,
      });
      setPreview(previewData);
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : "Failed to load preview");
      setPreview(null);
    } finally {
      setPreviewLoading(false);
    }
  }, [datasetId, previewPage, previewPageSize]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    loadPreview();
  }, [loadPreview]);

  const setTab = (tab: Tab) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("tab", tab);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const handleDeleteDataset = async () => {
    setDeleteDialogKind("dataset");
  };

  const handleDeleteVersion = async (version: DatasetVersion) => {
    setSelectedVersion(version);
    setDeleteDialogKind("version");
  };

  const confirmDelete = async () => {
    if (deleteDialogKind === "dataset") {
      if (!deleteSummary?.can_delete) {
        setActionError(
          deleteSummary?.blocking_reason ?? "Dataset cannot be deleted yet.",
        );
        setDeleteDialogKind(null);
        return;
      }

      setDeletingDataset(true);
      setActionError(null);
      try {
        await deleteDataset(dataset!.id);
        toast.success("Dataset deleted", `${dataset!.name} was removed.`);
        router.push(ROUTES.connections.datasets);
      } catch (err) {
        const message = err instanceof Error ? err.message : ERROR_MESSAGES.failedToDeleteDataset;
        setActionError(message);
        toast.danger("Delete failed", message);
      } finally {
        setDeletingDataset(false);
        setDeleteDialogKind(null);
      }
      return;
    }

    if (deleteDialogKind === "version" && selectedVersion) {
      if (selectedVersion.id === dataset!.active_version_id) {
        setActionError("Cannot delete active version");
        setDeleteDialogKind(null);
        return;
      }

      setDeletingVersionId(selectedVersion.id);
      setActionError(null);
      try {
        await deleteDatasetVersion(dataset!.id, selectedVersion.id);
        toast.success(
          "Version deleted",
          `v${selectedVersion.version_number} was removed from ${dataset!.name}.`,
        );
        await load();
        await loadPreview();
      } catch (err) {
        const message = err instanceof Error ? err.message : ERROR_MESSAGES.failedToDeleteVersion;
        setActionError(message);
        toast.danger("Delete failed", message);
      } finally {
        setDeletingVersionId(null);
        setDeleteDialogKind(null);
        setSelectedVersion(null);
      }
    }
  };

  if (loading) return <LoadingSpinner text={UI_LABELS.loading} />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!dataset) return <ErrorState message="Dataset not found" />;

  return (
    <>
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {editingName ? (
            <div className="flex items-center gap-2">
              <input
                ref={editNameRef}
                type="text"
                value={editNameValue}
                onChange={(e) => setEditNameValue(e.target.value)}
                onKeyDown={handleNameKeyDown}
                onBlur={() => { if (!savingName) handleSaveName(); }}
                disabled={savingName}
                className="w-full max-w-md rounded-md border border-zinc-300 bg-white px-3 py-1.5 text-xl font-semibold text-zinc-900 shadow-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500 disabled:cursor-wait disabled:opacity-60"
              />
              {savingName && (
                <LoadingSpinner className="size-4 shrink-0" />
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={handleStartEditName}
              className="group flex items-center gap-2 text-left"
              title="Click to rename dataset"
            >
              <h2 className="text-xl font-semibold text-zinc-900">{dataset!.name}</h2>
              <svg
                className="size-4 shrink-0 text-zinc-300 transition-colors group-hover:text-zinc-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
          )}
          <p className="mt-1 flex items-center gap-1.5 text-sm text-zinc-500">
            <span>{dataset!.source_object_name}</span>
            <span
              className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                DATASET_STATUS_COLORS[dataset!.status] || "bg-zinc-100 text-zinc-600"
              }`}
            >
              {dataset!.status}
            </span>
          </p>
          {deleteSummary && !deleteSummary.can_delete && (
            <NoticeBanner
              tone="warning"
              className="mt-3"
              title="Dataset delete is locked."
              description={`Remove active runs before deleting this dataset.${
                deleteSummary.blocking_reason ? ` ${deleteSummary.blocking_reason}` : ""
              }`}
            />
          )}
          {actionError && (
            <p className="mt-2 text-sm text-rose-600">{actionError}</p>
          )}
        </div>
        <button
          type="button"
          onClick={handleDeleteDataset}
          disabled={deletingDataset || !deleteSummary?.can_delete}
          title={
            deleteSummary?.can_delete
              ? "Delete dataset"
              : deleteSummary?.blocking_reason ?? "Dataset cannot be deleted yet."
          }
          className="rounded-md border border-rose-200 bg-white px-3 py-2 text-sm font-medium text-rose-700 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {deletingDataset ? UI_LABELS.deleting : "Delete Dataset"}
        </button>
      </div>

      <div className="border-b border-zinc-200">
        <nav className="flex gap-6">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setTab(tab)}
              className={`pb-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "border-b-2 border-zinc-900 text-zinc-900"
                  : "text-zinc-500 hover:text-zinc-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      <div>
        {activeTab === "Overview" && (
          <div className="space-y-6">
            <DatasetSummaryCards
              health={health}
              versionCount={versions.length}
              activeVersionNumber={activeVersionNumber}
            />
            <DatasetCharts
              columns={preview?.columns ?? []}
              rows={preview?.rows ?? []}
              loading={previewLoading}
              error={previewError}
            />
          </div>
        )}

        {activeTab === "Preview" && (
          <div className="flex min-h-0 flex-col gap-3">
            <span className="inline-block rounded-full border border-zinc-300 bg-zinc-50 px-2.5 py-0.5 text-xs font-medium text-zinc-500">
              Read only
            </span>
            <DatasetPreviewGrid
              columns={preview?.columns ?? []}
              rows={preview?.rows ?? []}
              totalRowCount={preview?.total_row_count ?? 0}
              page={previewPage}
              pageSize={previewPageSize}
              loading={previewLoading}
              error={previewError}
              onPageChange={(page) => setPreviewPage(page)}
              onRetry={loadPreview}
            />
          </div>
        )}

        {activeTab === "Schema" && (
          <div className="rounded-lg border border-zinc-200">
            <table className="min-w-full divide-y divide-zinc-200 text-sm">
              <thead>
                <tr className="bg-zinc-50">
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Column Name
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {preview?.columns.map((col) => (
                  <tr key={col} className="hover:bg-zinc-50">
                    <td className="px-4 py-2 font-medium text-zinc-900">{col}</td>
                    <td className="px-4 py-2 text-zinc-500">text</td>
                  </tr>
                ))}
                {(!preview || preview.columns.length === 0) && (
                  <tr>
                    <td colSpan={2} className="px-4 py-8 text-center text-sm text-zinc-500">
                      No schema information available
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "Transform" && (
          <div className="flex items-center justify-center py-16 text-sm text-zinc-500">
            Transform editor coming soon
          </div>
        )}

        {activeTab === "Lineage" && lineage && (
          <LineageView nodes={lineage.nodes} edges={lineage.edges} />
        )}

        {activeTab === "Runs" && (
          <RunHistory runs={runs} datasetId={datasetId} />
        )}

        {activeTab === "Versions" && (
            <VersionHistory
            versions={versions}
            activeVersionId={dataset!.active_version_id}
            onDeleteVersion={handleDeleteVersion}
            deletingVersionId={deletingVersionId}
            onRefreshLatest={handleRefreshLatest}
          />
        )}

        {activeTab === "Entity" && (
          <EntityTab dataset={dataset} versions={versions} />
        )}

        {activeTab === "Details" && (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 space-y-4">
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <h3 className="text-sm font-semibold text-zinc-900">Dataset Info</h3>
                <dl className="mt-3 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">ID</dt>
                    <dd className="text-zinc-900">{dataset!.id}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Created</dt>
                    <dd className="text-zinc-900">
                      {new Date(dataset.created_at).toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Updated</dt>
                    <dd className="text-zinc-900">
                      {new Date(dataset.updated_at).toLocaleString()}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Active Version</dt>
                    <dd className="text-zinc-900">
                      {dataset!.active_version_id
                        ? versions.find((v) => v.id === dataset!.active_version_id)
                            ?.version_number ?? dataset!.active_version_id.slice(0, 8)
                        : "None"}
                    </dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-zinc-500">Versions</dt>
                    <dd className="text-zinc-900">{versions.length}</dd>
                  </div>
                </dl>
              </div>

              {/* Sync Policy section */}
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-zinc-900">Sync Policy</h3>
                  {!editingSyncPolicy && (
                    <button
                      type="button"
                      onClick={() => setEditingSyncPolicy(true)}
                      className="text-xs font-medium text-zinc-500 hover:text-zinc-900"
                    >
                      Edit
                    </button>
                  )}
                </div>
                {editingSyncPolicy ? (
                  <div className="mt-3">
                    <SyncPolicyEditor
                      tableName={dataset!.name}
                      schemaColumns={[]}
                      detectedCursorColumn={dataset!.cursor_column ?? null}
                      supportsCdc={supportsCdc}
                      sourceType={connection?.source_type}
                      value={{
                        syncMode: (dataset!.sync_mode ?? "batch") as SyncPolicy["syncMode"],
                        batchStrategy: (dataset!.batch_strategy ?? "full_snapshot") as SyncPolicy["batchStrategy"],
                        realTimeStrategy: realTimeStrategyValue,
                        cursorColumn: dataset!.cursor_column ?? "",
                        frequencyMinutes: 1440,
                      }}
                      onChange={handleSaveSyncPolicy}
                    />
                    <div className="mt-3 flex gap-2">
                      <button
                        type="button"
                        onClick={() => setEditingSyncPolicy(false)}
                        disabled={savingSyncPolicy}
                        className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {UI_LABELS.cancel}
                      </button>
                      <span className="text-xs text-zinc-400">
                        Changes save automatically
                      </span>
                    </div>
                  </div>
                ) : (
                  <dl className="mt-3 space-y-2 text-sm">
                    <div className="flex justify-between">
                      <dt className="text-zinc-500">Sync Mode</dt>
                      <dd className="font-medium text-zinc-900">
                        {dataset!.sync_mode ?? "batch"}
                      </dd>
                    </div>
                    {dataset!.sync_mode === "batch" && (
                      <>
                        <div className="flex justify-between">
                          <dt className="text-zinc-500">Strategy</dt>
                          <dd className="text-zinc-900">
                            {dataset!.batch_strategy ?? "full_snapshot"}
                          </dd>
                        </div>
                        {dataset!.batch_strategy === "incremental_cursor" && (
                          <>
                            <div className="flex justify-between">
                              <dt className="text-zinc-500">Cursor Column</dt>
                              <dd className="text-zinc-900">
                                {dataset!.cursor_column ?? "—"}
                              </dd>
                            </div>
                            <div className="flex justify-between">
                              <dt className="text-zinc-500">Last Cursor Value</dt>
                              <dd className="text-xs text-zinc-400">
                                {dataset!.last_cursor_value ?? "—"}
                              </dd>
                            </div>
                          </>
                        )}
                      </>
                    )}
                    {dataset!.sync_mode === "direct_query" && (
                      <p className="text-xs text-zinc-400">
                        Live queries — no data copied
                      </p>
                    )}
                    {dataset!.sync_mode === "real_time" && (
                      <p className="text-xs text-zinc-500">
                        {dataset!.real_time_strategy === "cdc"
                          ? "True CDC (Streaming)"
                          : "Accelerated Polling"}
                      </p>
                    )}
                  </dl>
                )}
              </div>
            </div>
            <div className="lg:col-span-1">
              {health && <HealthPanel health={health} datasetId={datasetId} />}
            </div>
          </div>
        )}
      </div>
    </div>
    <input
      ref={fileInputRef}
      type="file"
      className="hidden"
      accept={FILE_ACCEPT}
      onChange={handleFileSelected}
    />
    {refreshingLatest && (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
        <div className="rounded-lg bg-white px-6 py-4 shadow-lg">
          <LoadingSpinner text="Refreshing latest data..." />
        </div>
      </div>
    )}
    <ConfirmDialog
      open={deleteDialogKind !== null}
      title={
        deleteDialogKind === "dataset"
          ? "Delete dataset?"
          : "Delete version?"
      }
      description={
        deleteDialogKind === "dataset"
          ? `Delete "${dataset!.name}" and all stored versions?`
          : selectedVersion
            ? `Delete version v${selectedVersion.version_number} from "${dataset!.name}"?`
            : undefined
      }
      confirmLabel={
        deleteDialogKind === "dataset"
          ? "Delete Dataset"
          : "Delete Version"
      }
      confirmTone="danger"
      busy={deletingDataset || deletingVersionId !== null}
      onConfirm={confirmDelete}
      onClose={() => {
        setDeleteDialogKind(null);
        setSelectedVersion(null);
      }}
    />
    </>
  );
}
export default DatasetWorkspaceContent;
