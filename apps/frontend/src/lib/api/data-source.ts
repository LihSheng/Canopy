import { request } from "./client";
import type {
  Project,
  SourceType,
  Connection,
  Dataset,
  DatasetVersion,
  Run,
  DatasetHealth,
  StaticFilePreview,
} from "./types";

export function fetchProjects(): Promise<Project[]> {
  return request<Project[]>("/api/v4/projects/");
}

export function fetchProject(id: string): Promise<Project> {
  return request<Project>(`/api/v4/projects/${id}`);
}

export function createProject(data: { name: string; description?: string }): Promise<Project> {
  return request<Project>("/api/v4/projects/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchSourceTypes(): Promise<SourceType[]> {
  return request<SourceType[]>("/api/v4/source-types/");
}

export function fetchConnections(projectId?: string): Promise<Connection[]> {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return request<Connection[]>(`/api/v4/connections/${qs}`);
}

export function fetchConnection(id: string): Promise<Connection> {
  return request<Connection>(`/api/v4/connections/${id}`);
}

export function createConnection(data: {
  project_id: string;
  source_type: string;
  name: string;
  config_json: Record<string, unknown>;
}): Promise<Connection> {
  return request<Connection>("/api/v4/connections/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function previewStaticFile(
  file: File,
  sourceType = "static_file",
): Promise<StaticFilePreview> {
  const form = new FormData();
  form.append("file", file);
  form.append("source_type", sourceType);

  return request<StaticFilePreview>("/api/v4/connections/preview", {
    body: form,
  });
}

export function fetchDatasets(projectId?: string, connectionId?: string): Promise<Dataset[]> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (connectionId) params.set("connection_id", connectionId);
  const qs = params.toString();
  return request<Dataset[]>(`/api/v4/datasets/${qs ? `?${qs}` : ""}`);
}

export function createDataset(data: {
  project_id: string;
  connection_id: string;
  name: string;
  source_object_name?: string;
}): Promise<Dataset> {
  return request<Dataset>("/api/v4/datasets/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchDataset(id: string): Promise<Dataset> {
  return request<Dataset>(`/api/v4/datasets/${id}`);
}

export function fetchDatasetVersions(datasetId: string): Promise<DatasetVersion[]> {
  return request<DatasetVersion[]>(`/api/v4/datasets/${datasetId}/versions`);
}

export function fetchDatasetPreview(datasetId: string): Promise<{ columns: string[]; rows: (string | number | boolean | null)[][]; total_row_count: number }> {
  return request<{ columns: string[]; rows: (string | number | boolean | null)[][]; total_row_count: number }>(
    `/api/v4/datasets/${datasetId}/preview`,
  );
}

export function fetchDatasetLineage(datasetId: string): Promise<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] }> {
  return request<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] }>(
    `/api/v4/datasets/${datasetId}/lineage`,
  );
}

export function fetchDatasetHealth(datasetId: string): Promise<DatasetHealth> {
  return request<DatasetHealth>(`/api/v4/datasets/${datasetId}/health`);
}

export function fetchRuns(datasetId?: string): Promise<Run[]> {
  const qs = datasetId ? `?dataset_id=${datasetId}` : "";
  return request<Run[]>(`/api/v4/runs/${qs}`);
}

export function fetchRun(id: string): Promise<Run> {
  return request<Run>(`/api/v4/runs/${id}`);
}

export function createRun(data: { dataset_id: string }): Promise<Run> {
  return request<Run>("/api/v4/runs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
