import { request } from "./client";
import type {
  Project,
  SourceType,
  Connection,
  ConnectionDependencySummary,
  ConnectionTestResult,
  Dataset,
  DatasetDeleteSummary,
  DatasetVersionDeleteSummary,
  DatasetVersion,
  DiscoveredTable,
  Run,
  DatasetHealth,
  DriftEvent,
  StaticFilePreview,
  SyncPolicyUpdate,
  TablePreview,
} from "./types";

export interface DatasetPreviewResponse {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  total_row_count: number;
  page: number;
  page_size: number;
}

export const fetchProjects = (): Promise<Project[]> => {
  return request<Project[]>("/api/projects/");
}

export const fetchProject = (id: string): Promise<Project> => {
  return request<Project>(`/api/projects/${id}`);
}

export const createProject = (data: { name: string; description?: string }): Promise<Project> => {
  return request<Project>("/api/projects/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export const fetchSourceTypes = (): Promise<SourceType[]> => {
  return request<SourceType[]>("/api/source-types/");
}

export const fetchConnections = (projectId?: string): Promise<Connection[]> => {
  const qs = projectId ? `?project_id=${projectId}` : "";
  return request<Connection[]>(`/api/connections/${qs}`);
}

export const fetchConnection = (id: string): Promise<Connection> => {
  return request<Connection>(`/api/connections/${id}`);
}

export type ConnectionLineageNode = { id: string; type: string; label: string; state?: "pending" | "materialized"; dataset_id?: string };
export type ConnectionLineageEdge = { from: string; to: string; type: string };

export const fetchConnectionLineage = (connectionId: string): Promise<{ nodes: ConnectionLineageNode[]; edges: ConnectionLineageEdge[] }> => {
  return request<{ nodes: ConnectionLineageNode[]; edges: ConnectionLineageEdge[] }>(
    `/api/connections/${connectionId}/lineage`,
  );
}

export const fetchConnectionDependencies = (id: string): Promise<ConnectionDependencySummary> => {
  return request<ConnectionDependencySummary>(`/api/connections/${id}/dependencies`);
}

export const createConnection = (data: {
  project_id: string;
  source_type: string;
  name: string;
  config_json: Record<string, unknown>;
}): Promise<Connection> => {
  return request<Connection>("/api/connections/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export const deleteConnection = (id: string): Promise<{ deleted: boolean; id: string }> => {
  return request<{ deleted: boolean; id: string }>(`/api/connections/${id}`, {
    method: "DELETE",
  });
}

export const previewStaticFile = async (
  file: File,
  sourceType = "static_file",
): Promise<StaticFilePreview> => {
  const form = new FormData();
  form.append("file", file);
  form.append("source_type", sourceType);

  return request<StaticFilePreview>("/api/connections/preview", {
    method: "POST",
    body: form,
  });
}

export const deleteStaticFilePreview = (sourceFilePath: string): Promise<{ deleted: boolean }> => {
  return request<{ deleted: boolean }>("/api/connections/preview", {
    method: "DELETE",
    body: JSON.stringify({ source_file_path: sourceFilePath }),
  });
}

export const fetchDatasets = (projectId?: string, connectionId?: string): Promise<Dataset[]> => {
  const params = new URLSearchParams();
  if (projectId) params.set("project_id", projectId);
  if (connectionId) params.set("connection_id", connectionId);
  const qs = params.toString();
  return request<Dataset[]>(`/api/datasets/${qs ? `?${qs}` : ""}`);
}

export const createDataset = (data: {
  project_id: string;
  connection_id: string;
  name: string;
  source_object_name?: string;
  defer_materialization?: boolean;
  sync_mode?: string | null;
  batch_strategy?: string | null;
  real_time_strategy?: string | null;
  cursor_column?: string | null;
}): Promise<Dataset> => {
  return request<Dataset>("/api/datasets/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export const fetchDataset = (id: string): Promise<Dataset> => {
  return request<Dataset>(`/api/datasets/${id}`);
}

export const fetchDatasetVersions = (datasetId: string): Promise<DatasetVersion[]> => {
  return request<DatasetVersion[]>(`/api/datasets/${datasetId}/versions`);
}

export const fetchDatasetPreview = (
  datasetId: string,
  params?: { page?: number; page_size?: number },
): Promise<DatasetPreviewResponse> => {
  const qs = new URLSearchParams();
  if (params?.page) qs.set("page", String(params.page));
  if (params?.page_size) qs.set("page_size", String(params.page_size));
  const query = qs.toString();
  return request<DatasetPreviewResponse>(
    `/api/datasets/${datasetId}/preview${query ? `?${query}` : ""}`,
  );
}

export type DatasetLineageNode = { id: string; type: string; label: string; state?: "pending" | "materialized" };
export type DatasetLineageEdge = { from: string; to: string; type: string };

export const fetchDatasetLineage = (datasetId: string): Promise<{ nodes: DatasetLineageNode[]; edges: DatasetLineageEdge[] }> => {
  return request<{ nodes: DatasetLineageNode[]; edges: DatasetLineageEdge[] }>(
    `/api/datasets/${datasetId}/lineage`,
  );
}

export const fetchDatasetHealth = (datasetId: string): Promise<DatasetHealth> => {
  return request<DatasetHealth>(`/api/datasets/${datasetId}/health`);
}

export const fetchDriftEvents = (datasetId: string, limit: number = 20): Promise<DriftEvent[]> => {
  return request<DriftEvent[]>(`/api/datasets/${datasetId}/drift-events?limit=${limit}`);
}

export const clearDriftBlock = (datasetId: string): Promise<{ id: string; status: string }> => {
  return request<{ id: string; status: string }>(`/api/datasets/${datasetId}/clear-drift-block`, {
    method: "POST",
    body: JSON.stringify({}),
    headers: { "Content-Type": "application/json" },
  });
}

export const fetchDatasetDeleteSummary = (datasetId: string): Promise<DatasetDeleteSummary> => {
  return request<DatasetDeleteSummary>(`/api/datasets/${datasetId}/dependencies`);
}

export const fetchDatasetVersionDeleteSummary = (
  datasetId: string,
  versionId: string,
): Promise<DatasetVersionDeleteSummary> => {
  return request<DatasetVersionDeleteSummary>(
    `/api/datasets/${datasetId}/versions/${versionId}/dependencies`,
  );
}

export const deleteDataset = (datasetId: string): Promise<{ deleted: boolean; id: string }> => {
  return request<{ deleted: boolean; id: string }>(`/api/datasets/${datasetId}`, {
    method: "DELETE",
  });
}

export const deleteDatasetVersion = (
  datasetId: string,
  versionId: string,
): Promise<{ deleted: boolean; id: string }> => {
  return request<{ deleted: boolean; id: string }>(`/api/datasets/${datasetId}/versions/${versionId}`, {
    method: "DELETE",
  });
}

export const updateDataset = (
  datasetId: string,
  data: { name: string },
): Promise<Dataset> => {
  return request<Dataset>(`/api/datasets/${datasetId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export const fetchRuns = (datasetId?: string): Promise<Run[]> => {
  const qs = datasetId ? `?dataset_id=${datasetId}` : "";
  return request<Run[]>(`/api/runs/${qs}`);
}

export const reimportDatasetVersion = (
  datasetId: string,
  data_path: string,
  columns: string[],
  sheet_name?: string,
): Promise<DatasetVersion> => {
  return request<DatasetVersion>(`/api/datasets/${datasetId}/reimport`, {
    method: "POST",
    body: JSON.stringify({ data_path, columns, sheet_name }),
  });
}

export const refreshDatasetVersion = (datasetId: string): Promise<DatasetVersion> => {
  return request<DatasetVersion>(`/api/datasets/${datasetId}/refresh`, {
    method: "POST",
  });
}

export const fetchRun = (id: string): Promise<Run> => {
  return request<Run>(`/api/runs/${id}`);
}

export const createRun = (data: { dataset_id: string }): Promise<Run> => {
  return request<Run>("/api/runs/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// --- Connection Wizard API ---

export const fetchConnectionTest = (id: string): Promise<ConnectionTestResult> => {
  return request<ConnectionTestResult>(`/api/connections/${id}/test`, {
    method: "POST",
  });
}

export const fetchTableDiscovery = (id: string): Promise<DiscoveredTable[]> => {
  return request<DiscoveredTable[]>(`/api/connections/${id}/discover`);
}

export const fetchTablePreview = (id: string, table: string): Promise<TablePreview> => {
  return request<TablePreview>(`/api/connections/${id}/discover/${encodeURIComponent(table)}`);
}

export const updateSyncPolicy = (id: string, policy: SyncPolicyUpdate): Promise<Dataset> => {
  return request<Dataset>(`/api/datasets/${id}/sync-policy`, {
    method: "PATCH",
    body: JSON.stringify(policy),
  });
}
