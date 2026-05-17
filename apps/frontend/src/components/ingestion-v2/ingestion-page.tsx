"use client";

import { useCallback, useEffect, useState } from "react";
import { CleaningRuleBuilder } from "./cleaning-rule-builder";
import { LineageGraph } from "./lineage-graph";
import { MappingReviewGrid } from "./mapping-review-grid";
import { PublishReview } from "./publish-review";
import { TemplateLibrary } from "./template-library";
import { UploadWizard } from "./upload-wizard";
import { WorkflowStepper, buildWorkflowSteps } from "./workflow-stepper";
import { WorkbookPreview } from "./workbook-preview";
import { fetchWorkflowState } from "@/lib/api/ingestion";

type VisibleSections = {
  preview: boolean;
  mapping: boolean;
  cleaning: boolean;
  templates: boolean;
  lineage: boolean;
  publish: boolean;
};

export function IngestionPageContent() {
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [pipelineId, setPipelineId] = useState<string | null>(null);
  const [boundVersionId, setBoundVersionId] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processedId, setProcessedId] = useState<string | null>(null);
  const [processError, setProcessError] = useState<string | null>(null);
  const [workflowStatus, setWorkflowStatus] = useState<string | null>(null);
  const [visible, setVisible] = useState<VisibleSections>({ preview: false, mapping: false, cleaning: false, templates: false, lineage: false, publish: false });

  const refreshWorkflow = useCallback(async (id: string) => {
    try {
      const state = await fetchWorkflowState(id);
      setWorkflowStatus(state.status);
    } catch {
      // workflow not yet available
    }
  }, []);

  const handleUploadComplete = (id: string) => {
    setUploadId(id);
    setVisible({ preview: true, mapping: false, cleaning: false, templates: false, lineage: false });
    refreshWorkflow(id);
  };

  const handleStepNavigate = (step: string) => {
    if (step === "mapping") setVisible((v) => ({ ...v, mapping: true }));
    if (step === "process") {
      const el = document.getElementById("process-section");
      el?.scrollIntoView({ behavior: "smooth" });
    }
    if (step === "publish") setVisible((v) => ({ ...v, publish: true }));
  };

  const handlePreviewReady = () => {
    if (uploadId) refreshWorkflow(uploadId);
  };

  const handleMappingsSaved = () => {
    if (uploadId) refreshWorkflow(uploadId);
  };

  const handlePipelineReady = (id: string) => {
    setPipelineId(id);
  };

  const handleTemplateBound = (versionId: string) => {
    setBoundVersionId(versionId);
  };

  const handleProcess = useCallback(async () => {
    if (!uploadId) return;
    setProcessing(true);
    setProcessError(null);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v3/ingestion/uploads/${uploadId}/process`,
        { method: "POST", credentials: "include" },
      );
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: "Processing failed" }));
        throw new Error(body.detail || `HTTP ${res.status}`);
      }
      const data = await res.json();
      setProcessedId(data.cleaned_snapshot_id);
      setVisible((v) => ({ ...v, lineage: true }));
      if (uploadId) refreshWorkflow(uploadId);
    } catch (err) {
      setProcessError(err instanceof Error ? err.message : "Processing failed");
    } finally {
      setProcessing(false);
    }
  }, [uploadId]);

  useEffect(() => {
    if (uploadId) {
      const timer = setInterval(() => refreshWorkflow(uploadId), 3000);
      return () => clearInterval(timer);
    }
  }, [uploadId, refreshWorkflow]);

  return (
    <div className="mx-auto max-w-2xl">
      {uploadId && (
        <div className="mb-6 rounded-xl border border-zinc-200 bg-white px-4 py-3">
          <WorkflowStepper steps={buildWorkflowSteps(workflowStatus, handleStepNavigate)} />
        </div>
      )}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-zinc-900">Upload Workbook</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Upload an Excel workbook to begin the ingestion workflow.
        </p>
      </div>

      <UploadWizard onUploadComplete={handleUploadComplete} />

      {uploadId && visible.preview && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Workbook Preview</h3>
          </div>
          <WorkbookPreview uploadId={uploadId} onPreviewReady={handlePreviewReady} />
          <div className="mt-4">
            <button
              onClick={() => setVisible((v) => ({ ...v, mapping: true }))}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
            >
              Review Column Mappings
            </button>
          </div>
        </div>
      )}

      {uploadId && visible.mapping && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Mapping Review</h3>
          </div>
          <MappingReviewGrid uploadId={uploadId} onMappingsSaved={handleMappingsSaved} />
          <div className="mt-4">
            <button
              onClick={() => setVisible((v) => ({ ...v, cleaning: true }))}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
            >
              Configure Cleaning Rules
            </button>
          </div>
        </div>
      )}

      {uploadId && visible.cleaning && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Cleaning Rules</h3>
          </div>
          <CleaningRuleBuilder uploadId={uploadId} onPipelineReady={handlePipelineReady} />
          <div className="mt-4">
            <button
              onClick={() => setVisible((v) => ({ ...v, templates: true }))}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
            >
              Select Template
            </button>
          </div>
        </div>
      )}

      {uploadId && pipelineId && visible.templates && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Template Library</h3>
          </div>
          <TemplateLibrary
            uploadId={uploadId}
            pipelineId={pipelineId}
            onBound={handleTemplateBound}
            currentBoundVersionId={boundVersionId}
          />
          {boundVersionId && (
            <div className="mt-3 space-y-3">
              <div className="rounded-xl border border-blue-200 bg-blue-50 p-3">
                <p className="text-sm font-semibold text-blue-800">
                  Template version bound to this upload.
                </p>
              </div>
              <button
                onClick={handleProcess}
                disabled={processing}
                className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800 disabled:opacity-50"
              >
                {processing ? "Processing..." : "Process Upload"}
              </button>
              {processError && (
                <p className="text-sm text-red-600">{processError}</p>
              )}
            </div>
          )}
        </div>
      )}

      {uploadId && visible.lineage && processedId && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Data Lineage</h3>
            <p className="text-xs text-zinc-500">
              Column-level provenance from raw file to ontology-ready fields.
            </p>
          </div>
          <LineageGraph uploadId={uploadId} />
          <div className="mt-6">
            <button
              onClick={() => setVisible((v) => ({ ...v, publish: true }))}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
            >
              Review &amp; Publish
            </button>
          </div>
        </div>
      )}

      {uploadId && visible.publish && (
        <div className="mt-6">
          <PublishReview uploadId={uploadId} />
        </div>
      )}
    </div>
  );
}
