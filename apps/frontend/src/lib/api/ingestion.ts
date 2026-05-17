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

export type MappingDecision = {
  source_column_name: string;
  target_field_name: string;
  confirmed: boolean;
  overridden_by_user: boolean;
};

export type MappingSuggestionsResult = {
  upload_id: string;
  decisions: MappingDecision[];
  column_profiles: ColumnProfile[];
};

export async function saveMapping(
  uploadId: string,
  decisions: MappingDecision[],
): Promise<MappingDecision[]> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/mapping`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(decisions),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to save mappings" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function fetchMappings(uploadId: string): Promise<MappingSuggestionsResult> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/mapping`, {
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to load mappings" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export type CleaningStep = {
  id: string;
  step_type: string;
  order: number;
  parameters: Record<string, unknown>;
  description: string | null;
};

export type CleaningPipeline = {
  id: string;
  upload_id: string;
  status: string;
  steps: CleaningStep[];
  created_at: string;
  updated_at: string;
};

export type CreatePipelineRequest = {
  upload_id: string;
};

export type ReorderStepsRequest = {
  step_ids: string[];
};

export async function createPipeline(uploadId: string): Promise<CleaningPipeline> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ upload_id: uploadId } as CreatePipelineRequest),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to create pipeline" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function fetchPipeline(pipelineId: string): Promise<CleaningPipeline> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}`, {
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to load pipeline" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function saveSteps(
  pipelineId: string,
  steps: Pick<CleaningStep, "step_type" | "order" | "parameters" | "description">[],
): Promise<CleaningStep[]> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}/steps`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(steps),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to save steps" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function reorderSteps(pipelineId: string, stepIds: string[]): Promise<CleaningStep[]> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}/steps/reorder`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ step_ids: stepIds } as ReorderStepsRequest),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to reorder steps" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function publishPipeline(pipelineId: string): Promise<CleaningPipeline> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}/publish`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to publish pipeline" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function validatePipeline(pipelineId: string): Promise<{ warnings: string[] }> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to validate pipeline" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
