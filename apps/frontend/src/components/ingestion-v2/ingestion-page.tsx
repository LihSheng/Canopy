"use client";

import { useState } from "react";
import { UploadWizard } from "./upload-wizard";
import { WorkbookPreview } from "./workbook-preview";

export function IngestionPageContent() {
  const [uploadId, setUploadId] = useState<string | null>(null);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-zinc-900">Upload Workbook</h2>
        <p className="mt-1 text-sm text-zinc-500">
          Upload an Excel workbook to begin the ingestion workflow.
        </p>
      </div>

      <UploadWizard onUploadComplete={setUploadId} />

      {uploadId && (
        <div className="mt-6">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-zinc-700">Workbook Preview</h3>
          </div>
          <WorkbookPreview uploadId={uploadId} />
        </div>
      )}
    </div>
  );
}
