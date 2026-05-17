"use client";

import { useState } from "react";
import { CleaningRuleBuilder } from "./cleaning-rule-builder";
import { MappingReviewGrid } from "./mapping-review-grid";
import { UploadWizard } from "./upload-wizard";
import { WorkbookPreview } from "./workbook-preview";

type VisibleSections = {
  preview: boolean;
  mapping: boolean;
  cleaning: boolean;
};

export function IngestionPageContent() {
  const [uploadId, setUploadId] = useState<string | null>(null);
  const [visible, setVisible] = useState<VisibleSections>({ preview: false, mapping: false, cleaning: false });

  const handleUploadComplete = (id: string) => {
    setUploadId(id);
    setVisible({ preview: true, mapping: false, cleaning: false });
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
          <CleaningRuleBuilder uploadId={uploadId} />
        </div>
      )}
    </div>
  );
}
