"use client";

import { useState } from "react";
import { CleaningRuleBuilder } from "./cleaning-rule-builder";
import { MappingReviewGrid } from "./mapping-review-grid";
import { TemplateLibrary } from "./template-library";
import { UploadWizard } from "./upload-wizard";
import { WorkbookPreview } from "./workbook-preview";

type VisibleSections = {
  preview: boolean;
  mapping: boolean;
  cleaning: boolean;
  templates: boolean;
};

export function IngestionPageContent() {
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [pipelineId, setPipelineId] = useState<string | null>(null);
  const [boundVersionId, setBoundVersionId] = useState<string | null>(null);
  const [visible, setVisible] = useState<VisibleSections>({ preview: false, mapping: false, cleaning: false, templates: false });

  const handleUploadComplete = (id: string) => {
    setUploadId(id);
    setVisible({ preview: true, mapping: false, cleaning: false, templates: false });
  };

  const handlePipelineReady = (id: string) => {
    setPipelineId(id);
  };

  const handleTemplateBound = (versionId: string) => {
    setBoundVersionId(versionId);
  };

  return (
    <div className="mx-auto max-w-2xl">
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
          <WorkbookPreview uploadId={uploadId} />
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
          <MappingReviewGrid uploadId={uploadId} />
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
            <div className="mt-3 rounded-xl border border-blue-200 bg-blue-50 p-3">
              <p className="text-sm font-semibold text-blue-800">
                Template version bound to this upload.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
