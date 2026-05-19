import { request } from "./client";
import type {
  Project,
  SourceType,
  Connection,
  ConnectionDependencySummary,
  Dataset,
  DatasetDeleteSummary,
  DatasetVersionDeleteSummary,
  DatasetVersion,
  Run,
  DatasetHealth,
  StaticFilePreview,
} from "./types";

export interface DatasetPreviewResponse {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  total_row_count: number;
  page: number;
  page_size: number;
}

export function fetchProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects/");
}

export function fetchProject(id: string): Promise<Project> {
  return request<Project>(`/api/projects/${id}`);
}

export function createProject(data: { name: string; description?: string }): Promise<Project> {
  return request<Project>("/api/projects/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchSourceTypes(): Promise<SourceType[]> {
  return request<SourceType[]>("/api/source-types/");
}

export function fetchConnections(projectId?: string): Promise<Connection[]> {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return request<Connection[]>(`/api/connections/${qs}`);
}

export function fetchConnection(id: string): Promise<Connection> {
  return request<Connection>(`/api/connections/${id}`);
}

export function fetchConnectionDependencies(id: string): Promise<ConnectionDependencySummary> {
  return request<ConnectionDependencySummary>(`/api/connections/${id}/dependencies`);
}

export function createConnection(data: {
  project_id: string;
  source_type: string;
  name: string;
  config_json: Record<string, unknown>;
}): Promise<Connection> {
  return request<Connection>("/api/connections/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function deleteConnection(id: string): Promise<{ deleted: boolean; id: string }> {
  return request<{ deleted: boolean; id: string }>(`/api/connections/${id}`, {
    method: "DELETE",
  });
}

export async function previewStaticFile(
  file: File,
  sourceType = "static_file",
): Promise<StaticFilePreview> {
  const form = new FormData();
  form.append("file", file);
  form.append("source_type", sourceType);

  return request<StaticFilePreview>("/api/connections/preview", {
    method: "POST",
    body: form,
  });
}

export function deleteStaticFilePreview(sourceFilePath: string): Promise<{ deleted: boolean }> {
  return request<{ deleted: boolean }>("/api/connections/preview", {
    method: "DELETE",
    body: JSON.stringify({ source_file_path: sourceFilePath }),
  });
}

export function fetchDatasets(projectId?: string, connectionId?: string): Promise<Dataset[]> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (connectionId) params.set("connection_id", connectionId);
  const qs = params.toString();
  return request<Dataset[]>(`/api/datasets/${qs ? `?${qs}` : ""}`);
}

export function createDataset(data: {
  project_id: string;
  connection_id: string;
  name: string;
  source_object_name?: string;
}): Promise<Dataset> {
  return request<Dataset>("/api/datasets/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchDataset(id: string): Promise<Dataset> {
  return request<Dataset>(`/api/datasets/${id}`);
}

export function fetchDatasetVersions(datasetId: string): Promise<DatasetVersion[]> {
  return request<DatasetVersion[]>(`/api/datasets/${datasetId}/versions`);
}

export function fetchDatasetPreview(
  datasetId: string,
  params?: { page?: number; page_size?: number },
): Promise<DatasetPreviewResponse> {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const query = qs.toString();
  return request<DatasetPreviewResponse>(
    `/api/datasets/${datasetId}/preview${query ? `?${query}` : ""}`,
  );
}

export function fetchDatasetLineage(datasetId: string): Promise<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] }> {
  return request<{ nodes: { id: string; type: string; label: string }[]; edges: { from: string; to: string; type: string }[] }>(
    `/api/datasets/${datasetId}/lineage`,
  );
}

export function fetchDatasetHealth(datasetId: string): Promise<DatasetHealth> {
  return request<DatasetHealth>(`/api/datasets/${datasetId}/health`);
}

export function fetchDatasetDeleteSummary(datasetId: string): Promise<DatasetDeleteSummary> {
  return request<DatasetDeleteSummary>(`/api/datasets/${datasetId}/dependencies`);
}

export function fetchDatasetVersionDeleteSummary(
  datasetId: string,
  versionId: string,
): Promise<DatasetVersionDeleteSummary> {
  return request<DatasetVersionDeleteSummary>(
    `/api/datasets/${datasetId}/versions/${versionId}/dependencies`,
  );
}

export function deleteDataset(datasetId: string): Promise<{ deleted: boolean; id: string }> {
  return request<{ deleted: boolean; id: string }>(`/api/datasets/${datasetId}`, {
    method: "DELETE",
  });
}

export function deleteDatasetVersion(
  datasetId: string,
  versionId: string,
): Promise<{ deleted: boolean; id: string }> {
  return request<{ deleted: boolean; id: string }>(`/api/datasets/${datasetId}/versions/${versionId}`, {
    method: "DELETE",
  });
}

export function fetchRuns(datasetId?: string): Promise<Run[]> {
  const qs = datasetId ? `?dataset_id=${datasetId}` : "";
  return request<Run[]>(`/api/runs/${qs}`);
}

export function reimportDatasetVersion(
  datasetId: string,
  data_path: string,
  columns: string[],
): Promise<DatasetVersion> {
  return request<DatasetVersion>(`/api/datasets/${datasetId}/reimport`, {
    method: "POST",
    body: JSON.stringify({ data_path, columns }),
  });
}

export function fetchRun(id: string): Promise<Run> {
  return request<Run>(`/api/runs/${id}`);
}

export function createRun(data: { dataset_id: string }): Promise<Run> {
  return request<Run>("/api/runs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
