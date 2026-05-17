"use client";

import { useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import {
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
  const sourceKey = searchParams.get("source") || "static_file";

  const [file, setFile] = useState<File | null>(null);
  const [preparing, setPreparing] = useState(false);
  const [preview, setPreview] = useState<StaticFilePreview | null>(null);
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const handleFileDrop = useCallback(async (dropped: File) => {
    setFile(dropped);
    setError(null);
    setPreparing(true);
    try {
      const result = await previewStaticFile(dropped, "static_file");
      setPreview(result);
      setSelectedSheets(new Set(result.sheet_profiles.map((s) => s.sheet_name)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setPreparing(false);
    }
  }, []);

  const toggleSheet = (name: string) => {
    setSelectedSheets((prev) => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

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
      />
      <div className="p-6">
        <div className="mx-auto max-w-2xl space-y-6">
          {!preview ? (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const f = e.dataTransfer.files[0];
                if (f) handleFileDrop(f);
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
                <label className="cursor-pointer text-indigo-600 hover:text-indigo-500">
                  browse
                  <input
                    type="file"
                    className="hidden"
                    accept=".xlsx,.csv"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) handleFileDrop(f);
                    }}
                  />
                </label>
              </p>
              <p className="mt-1 text-xs text-zinc-400">
                Excel (.xlsx) or CSV files
              </p>
            </div>
          ) : preparing ? (
            <LoadingSpinner text="Processing file..." />
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border border-zinc-200 bg-white p-4">
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
              </div>

              <div className="rounded-lg border border-zinc-200 bg-white">
                <div className="border-b border-zinc-100 px-4 py-3">
                  <h3 className="text-sm font-semibold text-zinc-900">
                    Select Sheets
                  </h3>
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
                          {sheet.row_count} rows, {sheet.column_count} columns
                        </p>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

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
