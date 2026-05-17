"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  type CleaningPipeline,
  type CleaningStep,
  createPipeline,
  fetchPipeline,
  publishPipeline,
  reorderSteps,
  saveSteps,
  validatePipeline,
} from "@/lib/api/ingestion";
import { ErrorState } from "@/components/shared/error-state";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

type BuilderState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "idle"; pipeline: CleaningPipeline; editingStepIndex: number | null }
  | { status: "saving" }
  | { status: "saved" };

type Props = {
  uploadId: string;
  onPipelineReady?: (pipelineId: string) => void;
};

const STEP_TYPE_OPTIONS = [
  { value: "trim", label: "Trim Whitespace", desc: "Trim whitespace from specified column values" },
  { value: "rename", label: "Rename Columns", desc: "Rename columns with new names" },
  { value: "cast", label: "Cast Column Types", desc: "Cast columns to target data types" },
  { value: "parse_date", label: "Parse Date", desc: "Parse date strings into standardized format" },
  { value: "dedupe", label: "Deduplicate Rows", desc: "Remove duplicate rows by columns" },
  { value: "normalize_nulls", label: "Normalize Nulls", desc: "Replace null-like values with replacement" },
  { value: "filter_empty_rows", label: "Filter Empty Rows", desc: "Filter rows exceeding null threshold" },
];

function defaultParameters(stepType: string): Record<string, unknown> {
  switch (stepType) {
    case "trim":
      return { columns: [] };
    case "rename":
      return { mappings: {} };
    case "cast":
      return { columns: {} };
    case "parse_date":
      return { columns: [], format: "%Y-%m-%d" };
    case "dedupe":
      return { columns: [], keep: "first" };
    case "normalize_nulls":
      return { columns: [], replace_with: "" };
    case "filter_empty_rows":
      return { threshold: 0.5 };
    default:
      return {};
  }
}

function stepTypeLabel(stepType: string): string {
  return STEP_TYPE_OPTIONS.find((o) => o.value === stepType)?.label ?? stepType;
}

function stepTypeDesc(stepType: string): string {
  return STEP_TYPE_OPTIONS.find((o) => o.value === stepType)?.desc ?? "";
}

function renderParametersEditor(
  stepType: string,
  params: Record<string, unknown>,
  onChange: (params: Record<string, unknown>) => void,
) {
  switch (stepType) {
    case "trim":
    case "normalize_nulls":
    case "dedupe":
    case "parse_date":
      return (
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500">Columns (comma-separated)</span>
          <input
            type="text"
            value={((params.columns ?? []) as string[]).join(", ")}
            onChange={(e) => onChange({ ...params, columns: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) })}
            className="rounded border border-zinc-300 px-2 py-1 text-sm"
            placeholder="col1, col2, col3"
          />
        </label>
      );
    case "rename":
      return (
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500">Rename mappings (old: new, one per line)</span>
          <textarea
            rows={3}
            value={Object.entries((params.mappings ?? {}) as Record<string, string>)
              .map(([k, v]) => `${k}: ${v}`)
              .join("\n")}
            onChange={(e) => {
              const mappings: Record<string, string> = {};
              for (const line of e.target.value.split("\n")) {
                const parts = line.split(":").map((s) => s.trim());
                if (parts.length >= 2 && parts[0]) mappings[parts[0]] = parts.slice(1).join(":").trim();
              }
              onChange({ ...params, mappings });
            }}
            className="rounded border border-zinc-300 px-2 py-1 text-sm"
            placeholder="old_name: new_name"
          />
        </label>
      );
    case "cast":
      return (
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500">Column type mappings (col: type, one per line)</span>
          <textarea
            rows={3}
            value={Object.entries((params.columns ?? {}) as Record<string, string>)
              .map(([k, v]) => `${k}: ${v}`)
              .join("\n")}
            onChange={(e) => {
              const columns: Record<string, string> = {};
              for (const line of e.target.value.split("\n")) {
                const parts = line.split(":").map((s) => s.trim());
                if (parts.length >= 2 && parts[0]) columns[parts[0]] = parts.slice(1).join(":").trim();
              }
              onChange({ ...params, columns });
            }}
            className="rounded border border-zinc-300 px-2 py-1 text-sm"
            placeholder="col_name: number|date|text"
          />
        </label>
      );
    case "filter_empty_rows":
      return (
        <label className="flex flex-col gap-1">
          <span className="text-xs text-zinc-500">Null threshold (0.0 - 1.0)</span>
          <input
            type="number"
            min="0"
            max="1"
            step="0.05"
            value={((params.threshold ?? 0.5) as number)}
            onChange={(e) => onChange({ ...params, threshold: parseFloat(e.target.value) || 0 })}
            className="rounded border border-zinc-300 px-2 py-1 text-sm"
          />
        </label>
      );
    default:
      return <p className="text-xs text-zinc-400">No editable parameters</p>;
  }
}

export function CleaningRuleBuilder({ uploadId, onPipelineReady }: Props) {
  const [state, setState] = useState<BuilderState>({ status: "loading" });
  const [pipelineId, setPipelineId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const pipeline = await createPipeline(uploadId);
      setPipelineId(pipeline.id);
      onPipelineReady?.(pipeline.id);
      setState({ status: "idle", pipeline, editingStepIndex: null });
    } catch {
      try {
        const existing = await fetchPipeline(pipelineId ?? "");
        if (existing) {
          setPipelineId(existing.id);
          onPipelineReady?.(existing.id);
          setState({ status: "idle", pipeline: existing, editingStepIndex: null });
          return;
        }
      } catch {
        // noop
      }
      setState({ status: "idle", pipeline: { id: "", upload_id: uploadId, status: "draft", steps: [], created_at: "", updated_at: "" }, editingStepIndex: null });
    }
  }, [uploadId, pipelineId, onPipelineReady]);

  useEffect(() => {
    const init = async () => {
      setState({ status: "loading" });
      try {
        const pipeline = await createPipeline(uploadId);
        setPipelineId(pipeline.id);
        onPipelineReady?.(pipeline.id);
        setState({ status: "idle", pipeline, editingStepIndex: null });
      } catch {
        setState({ status: "idle", pipeline: { id: "pending", upload_id: uploadId, status: "draft", steps: [], created_at: "", updated_at: "" }, editingStepIndex: null });
      }
    };
    init();
  }, [uploadId, onPipelineReady]);

  const handleAddStep = useCallback(
    (stepType: string) => {
      setState((prev) => {
        if (prev.status !== "idle") return prev;
        const newStep: CleaningStep = {
          id: `new-${Date.now()}`,
          step_type: stepType,
          order: prev.pipeline.steps.length,
          parameters: defaultParameters(stepType),
          description: stepTypeDesc(stepType),
        };
        return {
          ...prev,
          pipeline: { ...prev.pipeline, steps: [...prev.pipeline.steps, newStep] },
          editingStepIndex: prev.pipeline.steps.length,
        };
      });
    },
    [],
  );

  const handleRemoveStep = useCallback((index: number) => {
    setState((prev) => {
      if (prev.status !== "idle") return prev;
      const steps = prev.pipeline.steps.filter((_, i) => i !== index).map((s, i) => ({ ...s, order: i }));
      return { ...prev, pipeline: { ...prev.pipeline, steps }, editingStepIndex: null };
    });
  }, []);

  const handleMoveUp = useCallback((index: number) => {
    setState((prev) => {
      if (prev.status !== "idle" || index === 0) return prev;
      const steps = [...prev.pipeline.steps];
      [steps[index - 1], steps[index]] = [steps[index], steps[index - 1]];
      return { ...prev, pipeline: { ...prev.pipeline, steps: steps.map((s, i) => ({ ...s, order: i })) } };
    });
  }, []);

  const handleMoveDown = useCallback((index: number) => {
    setState((prev) => {
      if (prev.status !== "idle" || index >= prev.pipeline.steps.length - 1) return prev;
      const steps = [...prev.pipeline.steps];
      [steps[index], steps[index + 1]] = [steps[index + 1], steps[index]];
      return { ...prev, pipeline: { ...prev.pipeline, steps: steps.map((s, i) => ({ ...s, order: i })) } };
    });
  }, []);

  const handleSetEditing = useCallback((index: number | null) => {
    setState((prev) => {
      if (prev.status !== "idle") return prev;
      return { ...prev, editingStepIndex: index };
    });
  }, []);

  const handleUpdateParams = useCallback(
    (index: number, parameters: Record<string, unknown>) => {
      setState((prev) => {
        if (prev.status !== "idle") return prev;
        const steps = prev.pipeline.steps.map((s, i) => (i === index ? { ...s, parameters } : s));
        return { ...prev, pipeline: { ...prev.pipeline, steps } };
      });
    },
    [],
  );

  const handleSave = useCallback(async () => {
    if (state.status !== "idle" || !pipelineId) return;
    const currentPipeline = state.pipeline;
    setState({ status: "saving" });
    try {
      const stepsPayload = currentPipeline.steps.map((s) => ({
        step_type: s.step_type,
        order: s.order,
        parameters: s.parameters,
        description: s.description ?? stepTypeDesc(s.step_type),
      }));
      const saved = await saveSteps(pipelineId, stepsPayload);
      setState({ status: "saved" });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to save steps",
      });
    }
  }, [state, pipelineId]);

  const handlePublish = useCallback(async () => {
    if (!pipelineId) return;
    setState((prev) => {
      if (prev.status !== "idle") return prev;
      return { ...prev, status: "saving" };
    });
    try {
      const pipeline = await publishPipeline(pipelineId);
      setState({ status: "idle", pipeline, editingStepIndex: null });
    } catch (err) {
      setState({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to publish pipeline",
      });
    }
  }, [pipelineId]);

  const [addStepOpen, setAddStepOpen] = useState(false);

  const isPublished = state.status === "idle" && state.pipeline.status === "published";
  const hasSteps = state.status === "idle" && state.pipeline.steps.length > 0;

  if (state.status === "loading") return <LoadingSpinner text="Loading cleaning rules..." />;
  if (state.status === "error") return <ErrorState message={state.message} onRetry={load} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Cleaning Rules</h3>
        {isPublished && (
          <span className="inline-block rounded-full bg-green-100 px-3 py-0.5 text-xs font-semibold text-green-700">
            Published
          </span>
        )}
      </div>

      {state.status === "saved" && (
        <div className="rounded-xl border border-green-200 bg-green-50 p-3">
          <p className="text-sm font-semibold text-green-800">Steps saved.</p>
        </div>
      )}

      {!hasSteps && !isPublished && (
        <p className="text-sm text-zinc-400">No cleaning rules configured yet.</p>
      )}

      {state.status === "idle" && (
        <div className="space-y-2">
          {state.pipeline.steps.map((step, i) => (
            <div
              key={step.id}
              className="rounded-xl border border-zinc-200 bg-white"
            >
              <div className="flex items-center gap-2 px-3 py-2">
                <span className="flex h-6 w-6 items-center justify-center rounded bg-zinc-100 text-xs font-semibold text-zinc-500">
                  {i + 1}
                </span>
                <span className="text-sm font-semibold text-zinc-800">{stepTypeLabel(step.step_type)}</span>
                {step.description && (
                  <span className="text-xs text-zinc-400">{step.description}</span>
                )}
                <div className="ml-auto flex gap-1">
                  {!isPublished && (
                    <>
                      <button
                        onClick={() => handleSetEditing(state.editingStepIndex === i ? null : i)}
                        className="rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100"
                      >
                        {state.editingStepIndex === i ? "Done" : "Edit"}
                      </button>
                      <button
                        onClick={() => handleMoveUp(i)}
                        disabled={i === 0}
                        className="rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100 disabled:opacity-30"
                        title="Move up"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => handleMoveDown(i)}
                        disabled={i >= state.pipeline.steps.length - 1}
                        className="rounded px-2 py-1 text-xs text-zinc-500 hover:bg-zinc-100 disabled:opacity-30"
                        title="Move down"
                      >
                        ↓
                      </button>
                      <button
                        onClick={() => handleRemoveStep(i)}
                        className="rounded px-2 py-1 text-xs text-red-500 hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </>
                  )}
                </div>
              </div>
              {state.editingStepIndex === i && !isPublished && (
                <div className="border-t border-zinc-100 px-3 py-2">
                  {renderParametersEditor(step.step_type, step.parameters, (p) => handleUpdateParams(i, p))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {!isPublished && (
        <div className="flex items-center gap-2">
          {addStepOpen ? (
            <div className="flex flex-wrap gap-1">
              {STEP_TYPE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    handleAddStep(opt.value);
                    setAddStepOpen(false);
                  }}
                  className="rounded-lg border border-zinc-300 px-2 py-1 text-xs text-zinc-700 transition-colors hover:bg-zinc-50"
                >
                  {opt.label}
                </button>
              ))}
              <button
                onClick={() => setAddStepOpen(false)}
                className="rounded-lg px-2 py-1 text-xs text-zinc-400 hover:text-zinc-600"
              >
                Cancel
              </button>
            </div>
          ) : (
            <button
              onClick={() => setAddStepOpen(true)}
              className="rounded-lg border border-dashed border-zinc-300 px-3 py-1.5 text-xs font-semibold text-zinc-500 transition-colors hover:border-zinc-400 hover:text-zinc-700"
            >
              + Add Step
            </button>
          )}
        </div>
      )}

      {!isPublished && (
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={state.status === "saving"}
            className="rounded-lg bg-zinc-900 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {state.status === "saving" ? "Saving..." : "Save Steps"}
          </button>
          <button
            onClick={handlePublish}
            disabled={!hasSteps}
            className="rounded-lg bg-green-700 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-green-600 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Publish Pipeline
          </button>
        </div>
      )}
    </div>
  );
}
