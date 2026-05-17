import { request } from "./client";
import type {
  Project,
  SourceType,
  Connection,
  Dataset,
  DatasetVersion,
  Run,
  DatasetHealth,
} from "./types";

export function fetchProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects");
}

export function fetchProject(id: string): Promise<Project> {
  return request<Project>(`/api/projects/${id}`);
}

export function createProject(data: { name: string; description?: string }): Promise<Project> {
  return request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchSourceTypes(): Promise<SourceType[]> {
  return request<SourceType[]>("/api/source-types");
}

export function fetchConnections(projectId?: string): Promise<Connection[]> {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return request<Connection[]>(`/api/connections${qs}`);
}

export function fetchConnection(id: string): Promise<Connection> {
  return request<Connection>(`/api/connections/${id}`);
}

export function createConnection(data: {
  project_id: string;
  source_type: string;
  name: string;
  config_json: Record<string, unknown>;
}): Promise<Connection> {
  return request<Connection>("/api/connections", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function fetchDatasets(projectId?: string, connectionId?: string): Promise<Dataset[]> {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (connectionId) params.set("connection_id", connectionId);
  const qs = params.toString();
  return request<Dataset[]>(`/api/datasets${qs ? `?${qs}` : ""}`);
}

export function createDataset(data: {
  project_id: string;
  connection_id: string;
  name: string;
  source_object_name?: string;
}): Promise<Dataset> {
  return request<Dataset>("/api/datasets", {
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

export function fetchDatasetPreview(datasetId: string): Promise<{ columns: string[]; rows: (string | null)[][]; total_row_count: number }> {
  return request<{ columns: string[]; rows: (string | null)[][]; total_row_count: number }>(
    `/api/datasets/${datasetId}/preview`,
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

export function fetchRuns(datasetId?: string): Promise<Run[]> {
  const qs = datasetId ? `?dataset_id=${datasetId}` : "";
  return request<Run[]>(`/api/runs${qs}`);
}

export function fetchRun(id: string): Promise<Run> {
  return request<Run>(`/api/runs/${id}`);
}

export function createRun(data: { dataset_id: string }): Promise<Run> {
  return request<Run>("/api/runs", {
    method: "POST",
    body: JSON.stringify(data),
  });
}
