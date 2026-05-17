"use client";

import { useCallback, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { buildConnectionsBreadcrumbs } from "@/components/analytics-shell/breadcrumb-helpers";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { PreviewGrid } from "@/components/preview-grid";
import {
  deleteStaticFilePreview,
  previewStaticFile,
  fetchProjects,
  createProject,
  createConnection,
  createDataset,
} from "@/lib/api/data-source";
import type { StaticFilePreview } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

export default function SetupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const file_input_ref = useRef<HTMLInputElement | null>(null);
  const sourceKey = searchParams.get("source") || "static_file";

  const [file, setFile] = useState<File | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [preview, setPreview] = useState<StaticFilePreview | null>(null);
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());
  const [activeSheetName, setActiveSheetName] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const handleFileDrop = useCallback(async (dropped: File) => {
    setFile(dropped);
    setError(null);
    setPreparing(true);
    try {
      const result = await previewStaticFile(dropped, "static_file");
      setPreview(result);
      const sheetNames = result.sheet_profiles.map((s) => s.sheet_name);
      setSelectedSheets(new Set(sheetNames));
      setActiveSheetName(sheetNames[0] || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setPreparing(false);
    }
  }, []);

  const handleFileReset = async () => {
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
    if (file_input_ref.current) {
      file_input_ref.current.value = "";
    }
  };

  const toggleSheet = (name: string) => {
    setSelectedSheets((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      if (activeSheetName === name && !next.has(name)) {
        setActiveSheetName(next.values().next().value || "");
      }
      return next;
    });
  };

  const activeSheet = preview?.sheet_profiles.find((sheet) => sheet.sheet_name === activeSheetName) || null;

  const handleCreateDatasets = useCallback(async () => {
    if (!preview) return;
    setCreating(true);
    setError(null);
    try {
      const projects = await fetchProjects();
      let projectId: string;
      if (projects.length > 0) {
        projectId = projects[0].id;
      } else {
        const project = await createProject({ name: "Default Project" });
        projectId = project.id;
      }

      const connection = await createConnection({
        project_id: projectId,
        source_type: "static_file",
        name: file?.name || preview.file_name || "Static File",
        config_json: {
          file_name: preview.file_name,
          source_file_path: preview.source_file_path,
        },
      });

      const selected = preview.sheet_profiles.filter((s) => selectedSheets.has(s.sheet_name));
      for (const sheet of selected) {
        await createDataset({
          project_id: projectId,
          connection_id: connection.id,
          name: sheet.sheet_name,
          source_object_name: sheet.sheet_name,
        });
      }
      router.push("/dashboard/connections/datasets");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create datasets");
    } finally {
      setCreating(false);
    }
  }, [preview, selectedSheets, file, router]);

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <AnalyticsHeader
        title="Connection Setup"
        contextText={`Source: ${sourceKey}`}
        actions={
          <Link
            href="/dashboard/connections/sources"
            className="rounded-md border border-zinc-200 px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Back to sources
          </Link>
        }
      />
      <AnalyticsBreadcrumb
        items={buildConnectionsBreadcrumbs(
          { label: "Source Catalog", href: "/dashboard/connections/sources" },
          { label: "Connection Setup" },
        )}
      />
      <div className="p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          <input
            ref={file_input_ref}
            type="file"
            className="hidden"
            accept=".xlsx,.csv"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                void handleFileDrop(f);
                e.currentTarget.value = "";
              }
            }}
          />
          {preparing ? (
            <LoadingSpinner text="Processing file..." />
          ) : !preview ? (
            <div className="space-y-3">
              <div
                role="button"
                tabIndex={0}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  const f = e.dataTransfer.files[0];
                  if (f) void handleFileDrop(f);
                }}
                onClick={() => file_input_ref.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    file_input_ref.current?.click();
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
              {error && <ErrorState message={error} />}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <svg
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="h-8 w-8 text-green-600"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <div>
                      <p className="text-sm font-medium text-zinc-900">{file?.name}</p>
                      <p className="text-xs text-zinc-500">
                        {preview.sheet_profiles.length} sheet
                        {preview.sheet_profiles.length !== 1 ? "s" : ""} detected
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      void handleFileReset();
                    }}
                    className="rounded-md border border-zinc-200 px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
                  >
                    Remove file
                  </button>
                </div>
              </div>

              <div className="rounded-lg border border-zinc-200 bg-white">
                <div className="border-b border-zinc-100 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-sm font-semibold text-zinc-900">
                      Select Sheets
                    </h3>
                    <label className="flex items-center gap-2 text-xs text-zinc-500">
                      Preview
                      <select
                        value={activeSheetName}
                        onChange={(e) => setActiveSheetName(e.target.value)}
                        className="rounded-md border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 focus:border-zinc-400 focus:outline-none"
                      >
                        {preview.sheet_profiles.map((sheet) => (
                          <option key={sheet.sheet_name} value={sheet.sheet_name}>
                            {sheet.sheet_name}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                </div>
                <div className="space-y-1 p-2">
                  {preview.sheet_profiles.map((sheet) => (
                    <label
                      key={sheet.sheet_name}
                      className="flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 transition-colors hover:bg-zinc-50"
                    >
                      <input
                        type="checkbox"
                        checked={selectedSheets.has(sheet.sheet_name)}
                        onChange={() => toggleSheet(sheet.sheet_name)}
                        className="h-4 w-4 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-900"
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-zinc-900">
                          {sheet.sheet_name}
                        </p>
                        <p className="text-xs text-zinc-500">
                          {sheet.data_row_count} data rows, {sheet.column_count} columns
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {activeSheet && (
                <div className="space-y-2 rounded-lg border border-zinc-200 bg-white p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-zinc-900">
                        Preview: {activeSheet.sheet_name}
                      </h3>
                      <p className="text-xs text-zinc-500">
                        {activeSheet.preview_rows.length} sample rows of {activeSheet.data_row_count} data rows
                      </p>
                    </div>
                    <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
                      Read only
                    </span>
                  </div>
                  <PreviewGrid
                    columns={activeSheet.preview_columns}
                    rows={activeSheet.preview_rows}
                    totalRowCount={activeSheet.data_row_count}
                  />
                </div>
              )}

              {error && <ErrorState message={error} />}

              <button
                onClick={handleCreateDatasets}
                disabled={selectedSheets.size === 0 || creating}
                className="w-full rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {creating
                  ? "Creating datasets..."
                  : `Create Datasets (${selectedSheets.size})`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
