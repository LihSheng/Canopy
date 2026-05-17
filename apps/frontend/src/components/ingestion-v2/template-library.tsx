"use client";

import { useCallback, useEffect, useState } from "react";
import {
  type TemplateFamily,
  type TemplateFamilyDetail,
  type TemplateVersion,
  bindPipelineToTemplate,
  createTemplateFamily,
  createTemplateVersion,
  fetchTemplateFamilies,
  fetchTemplateFamily,
  publishTemplateVersion,
} from "@/lib/api/ingestion";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

type LibraryState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "list"; families: TemplateFamily[]; filterDataset: string; filterSource: string }
  | { status: "detail"; family: TemplateFamilyDetail; selectedVersionId: string | null }
  | { status: "create" };

type Props = {
  uploadId: string;
  pipelineId: string;
  datasetType?: string;
  sourceProfile?: string;
  onBound: (versionId: string) => void;
  currentBoundVersionId?: string | null;
  pipelineSteps?: Record<string, unknown>[];
};

export function TemplateLibrary({
  uploadId,
  pipelineId,
  datasetType,
  sourceProfile,
  onBound,
  currentBoundVersionId,
  pipelineSteps,
}: Props) {
  const [state, setState] = useState<LibraryState>({ status: "loading" });
  const [createName, setCreateName] = useState("");
  const [createDesc, setCreateDesc] = useState("");

  const load = useCallback(async (filterDataset?: string, filterSource?: string) => {
    setState({ status: "loading" });
    try {
      const families = await fetchTemplateFamilies(filterDataset, filterSource);
      setState({
        status: "list",
        families,
        filterDataset: filterDataset ?? "",
        filterSource: filterSource ?? "",
      });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load template families",
      });
    }
  }, []);

  useEffect(() => {
    load(datasetType, sourceProfile);
  }, [load, datasetType, sourceProfile]);

  const handleViewDetail = useCallback(async (templateId: string) => {
    setState({ status: "loading" });
    try {
      const family = await fetchTemplateFamily(templateId);
      setState({ status: "detail", family, selectedVersionId: null });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load template family",
      });
    }
  }, []);

  const handleCreateFamily = useCallback(async () => {
    if (!createName.trim() || !datasetType || !sourceProfile) return;
    setState({ status: "loading" });
    try {
      await createTemplateFamily({
        dataset_type: datasetType,
        source_profile: sourceProfile,
        name: createName.trim(),
        description: createDesc.trim(),
      });
      setCreateName("");
      setCreateDesc("");
      await load(datasetType, sourceProfile);
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to create template family",
      });
    }
  }, [createName, createDesc, datasetType, sourceProfile, load]);

  const handleCreateVersion = useCallback(async (templateId: string, cloneFrom?: string) => {
    try {
      const spec = cloneFrom ? undefined : { steps: pipelineSteps ?? [] };
      const version = await createTemplateVersion(templateId, {
        clone_from_version_id: cloneFrom ?? null,
        spec_json: spec ?? {},
      });
      const family = await fetchTemplateFamily(templateId);
      setState({ status: "detail", family, selectedVersionId: version.id });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to create version",
      });
    }
  }, [pipelineSteps]);

  const handlePublish = useCallback(async (templateId: string, versionId: string) => {
    try {
      const version = await publishTemplateVersion(templateId, versionId);
      const family = await fetchTemplateFamily(templateId);
      setState({ status: "detail", family, selectedVersionId: version.id });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to publish version",
      });
    }
  }, []);

  const handleBind = useCallback(async (versionId: string) => {
    try {
      await bindPipelineToTemplate(pipelineId, versionId);
      onBound(versionId);
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to bind template",
      });
    }
  }, [pipelineId, onBound]);

  if (state.status === "loading") return <LoadingSpinner text="Loading template library..." />;
  if (state.status === "error") return <ErrorState message={state.message} onRetry={() => load()} />;

  if (state.status === "create") {
    return (
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-zinc-700">New Template Family</h3>
        <div className="space-y-3">
          <label className="flex flex-col gap-1">
            <span className="text-xs text-zinc-500">Name</span>
            <input
              type="text"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              className="rounded border border-zinc-300 px-2 py-1 text-sm"
              placeholder="e.g. Payroll Standard"
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="text-xs text-zinc-500">Description</span>
            <textarea
              rows={2}
              value={createDesc}
              onChange={(e) => setCreateDesc(e.target.value)}
              className="rounded border border-zinc-300 px-2 py-1 text-sm"
              placeholder="Optional description"
            />
          </label>
          <div className="flex gap-2">
            <button
              onClick={handleCreateFamily}
              disabled={!createName.trim()}
              className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => load()}
              className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (state.status === "detail") {
    const { family } = state;
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-zinc-700">{family.name}</h3>
            <p className="text-xs text-zinc-400">{family.dataset_type} / {family.source_profile}</p>
            {family.description && (
              <p className="mt-1 text-xs text-zinc-500">{family.description}</p>
            )}
          </div>
          <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${
            family.status === "active" ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
          }`}>
            {family.status}
          </span>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => handleCreateVersion(family.id)}
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800"
          >
            New Draft Version
          </button>
          <button
            onClick={() => load()}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
          >
            Back
          </button>
        </div>

        <div className="space-y-2">
          {family.versions.length === 0 && (
            <p className="text-xs text-zinc-400">No versions yet.</p>
          )}
          {family.versions.map((v) => (
            <div
              key={v.id}
              className={`rounded-xl border p-3 ${
                state.selectedVersionId === v.id ? "border-zinc-400 bg-zinc-50" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-semibold text-zinc-800">v{v.version_number}</span>
                  <span className={`ml-2 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                    v.state === "published" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"
                  }`}>
                    {v.state}
                  </span>
                  {v.published_at && (
                    <span className="ml-2 text-xs text-zinc-400">
                      {new Date(v.published_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
                <div className="flex gap-1">
                  {v.state === "draft" && (
                    <button
                      onClick={() => handlePublish(family.id, v.id)}
                      className="rounded px-2 py-1 text-xs font-semibold text-green-700 hover:bg-green-50"
                    >
                      Publish
                    </button>
                  )}
                  {v.state === "published" && (
                    <button
                      onClick={() => handleBind(v.id)}
                      disabled={currentBoundVersionId === v.id}
                      className="rounded px-2 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {currentBoundVersionId === v.id ? "Bound" : "Bind to Upload"}
                    </button>
                  )}
                </div>
              </div>
              {(v.spec_json as { steps?: unknown[] })?.steps && (
                <p className="mt-1 text-xs text-zinc-400">
                  {(v.spec_json as { steps: unknown[] }).steps.length} step(s)
                </p>
              )}
            </div>
          ))}
        </div>

        {family.versions.some((v) => v.state === "published") && (
          <div className="border-t border-zinc-200 pt-3">
            <button
              onClick={() => handleCreateVersion(family.id, family.versions.find((v) => v.state === "published")?.id)}
              className="rounded-lg border border-dashed border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-500 transition-colors hover:border-zinc-400 hover:text-zinc-700"
            >
              + Clone from Latest Published
            </button>
          </div>
        )}
      </div>
    );
  }

  const { families, filterDataset, filterSource } = state;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Template Library</h3>
        <button
          onClick={() => setState({ status: "create" })}
          className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800"
        >
          + New Template
        </button>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={filterDataset}
          onChange={(e) => load(e.target.value || undefined, filterSource || undefined)}
          placeholder="Filter by dataset type"
          className="flex-1 rounded border border-zinc-300 px-2 py-1 text-xs"
        />
        <input
          type="text"
          value={filterSource}
          onChange={(e) => load(filterDataset || undefined, e.target.value || undefined)}
          placeholder="Filter by source profile"
          className="flex-1 rounded border border-zinc-300 px-2 py-1 text-xs"
        />
      </div>

      {families.length === 0 && (
        <p className="text-sm text-zinc-400">No template families found.</p>
      )}

      <div className="space-y-2">
        {families.map((f) => (
          <button
            key={f.id}
            onClick={() => handleViewDetail(f.id)}
            className="w-full rounded-xl border border-zinc-200 bg-white p-3 text-left transition-colors hover:bg-zinc-50"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-zinc-800">{f.name}</span>
              <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                f.status === "active" ? "bg-green-100 text-green-700" : "bg-zinc-100 text-zinc-500"
              }`}>
                {f.status}
              </span>
            </div>
            <p className="mt-0.5 text-xs text-zinc-400">{f.dataset_type} / {f.source_profile}</p>
            {f.description && (
              <p className="mt-1 text-xs text-zinc-500">{f.description}</p>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
