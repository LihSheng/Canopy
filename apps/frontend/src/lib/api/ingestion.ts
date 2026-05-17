const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type UploadResult = {
  upload_id: string;
  status: string;
  file_name: string;
  file_size: number;
  checksum: string;
  created_at: string;
};

export async function uploadFile(
  file: File,
  sourceProfile: string,
  datasetType: string,
): Promise<UploadResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("source_profile", sourceProfile);
  form.append("dataset_type", datasetType);

  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads`, {
    method: "POST",
    credentials: "include",
    body: form,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export type ColumnProfile = {
  source_column_name: string;
  inferred_type: string;
  sample_values: string[];
  null_ratio: number;
  confidence: number;
  suggested_target_field: string | null;
};

export type SheetProfile = {
  sheet_name: string;
  row_count: number;
  column_count: number;
  header_row_index: number | null;
  confidence: number;
  warnings: string[];
};

export type WorkbookProfile = {
  upload_id: string;
  best_sheet_name: string | null;
  sheet_profiles: SheetProfile[];
  column_profiles: ColumnProfile[];
  preview_rows: (string | null)[][];
  warnings: string[];
};

export async function fetchPreview(uploadId: string): Promise<WorkbookProfile> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/preview`, {
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to load preview" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
