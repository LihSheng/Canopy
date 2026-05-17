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

export type TemplateFamily = {
  id: string;
  dataset_type: string;
  source_profile: string;
  name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type TemplateVersion = {
  id: string;
  template_id: string;
  version_number: number;
  state: string;
  spec_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  published_at: string | null;
};

export type TemplateFamilyDetail = TemplateFamily & {
  versions: TemplateVersion[];
};

export type CreateTemplateVersionReq = {
  clone_from_version_id?: string | null;
  spec_json?: Record<string, unknown>;
};

export type BindTemplateReq = {
  template_version_id: string;
};

export async function fetchTemplateFamilies(
  datasetType?: string,
  sourceProfile?: string,
): Promise<TemplateFamily[]> {
  const params = new URLSearchParams();
  if (datasetType) params.set("dataset_type", datasetType);
  if (sourceProfile) params.set("source_profile", sourceProfile);
  const qs = params.toString();
  const url = `${API_BASE}/api/v3/ingestion/template-families${qs ? "?" + qs : ""}`;
  const res = await fetch(url, { credentials: "include" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch template families" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function createTemplateFamily(
  data: { dataset_type: string; source_profile: string; name: string; description?: string },
): Promise<TemplateFamily> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/template-families`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to create template family" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchTemplateFamily(templateId: string): Promise<TemplateFamilyDetail> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/template-families/${templateId}`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch template family" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchTemplateVersions(templateId: string): Promise<{ template_id: string; versions: TemplateVersion[] }> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/template-families/${templateId}/versions`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch template versions" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchTemplateVersion(templateId: string, versionId: string): Promise<TemplateVersion> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/template-families/${templateId}/versions/${versionId}`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch template version" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function createTemplateVersion(
  templateId: string,
  data: CreateTemplateVersionReq,
): Promise<TemplateVersion> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/template-families/${templateId}/versions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to create template version" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function publishTemplateVersion(
  templateId: string,
  versionId: string,
): Promise<TemplateVersion> {
  const res = await fetch(
    `${API_BASE}/api/v3/ingestion/template-families/${templateId}/versions/${versionId}/publish`,
    { method: "POST", credentials: "include" },
  );
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to publish template version" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export type LineageNode = {
  id: string;
  node_type: string;
  label: string;
  metadata: Record<string, unknown>;
};

export type LineageEdge = {
  id: string;
  from_node_id: string;
  to_node_id: string;
  edge_type: string;
  metadata: Record<string, unknown>;
};

export type LineageGraphResult = {
  upload_id: string;
  nodes: LineageNode[];
  edges: LineageEdge[];
};

export async function fetchLineage(uploadId: string): Promise<LineageGraphResult> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/lineage`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to load lineage" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export type PublishValidationResult = {
  valid: boolean;
  warnings: string[];
  errors: string[];
};

export type PublishRecord = {
  id: string;
  upload_id: string;
  cleaned_snapshot_id: string;
  template_version_id: string;
  status: string;
  published_at: string | null;
  published_by: string | null;
  validation_errors: string[];
  validation_warnings: string[];
  created_at: string;
};

export type PublishHistory = {
  records: PublishRecord[];
};

export async function publishUpload(uploadId: string): Promise<PublishRecord> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/publish`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to publish" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function fetchPublishState(uploadId: string): Promise<PublishRecord | null> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/publish`, {
    credentials: "include",
  });
  if (!res.ok) {
    if (res.status === 404) return null;
    const body = await res.json().catch(() => ({ detail: "Failed to fetch publish state" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  const data = await res.json();
  return data;
}

export async function fetchPublishHistory(uploadId: string): Promise<PublishHistory> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/publish/history`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch publish history" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export type CleanedSnapshotResult = {
  id: string;
  upload_id: string;
  template_version_id: string;
  status: string;
  row_count: number;
  warning_count: number;
  warnings: string[];
  created_at: string;
};

export async function fetchCleanedSnapshot(uploadId: string): Promise<CleanedSnapshotResult> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/uploads/${uploadId}/cleaned`, {
    credentials: "include",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to fetch cleaned snapshot" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function bindPipelineToTemplate(
  pipelineId: string,
  templateVersionId: string,
): Promise<CleaningPipeline> {
  const res = await fetch(`${API_BASE}/api/v3/ingestion/templates/${pipelineId}/bind`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ template_version_id: templateVersionId } as BindTemplateReq),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Failed to bind pipeline to template" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}
