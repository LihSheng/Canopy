import { request } from "./client";
import type {
  EntityRegistryItem,
  EntityDetail,
  EntityRevision,
  EntityStatus,
  EntityRevisionProperty,
} from "./types";

export const fetchEntities = (search?: string): Promise<EntityRegistryItem[]> => {
  const params = new URLSearchParams();
  if (search) params.set("q", search);
  const qs = params.toString();
  return request<EntityRegistryItem[]>(`/api/entities${qs ? `?${qs}` : ""}`);
};

export const fetchEntity = (id: string): Promise<EntityDetail> => {
  return request<EntityDetail>(`/api/entities/${id}`);
};

// ─── Entity Revision APIs ───

export const fetchEntityStatus = (entityId: string): Promise<EntityStatus> => {
  return request<EntityStatus>(`/api/entities/${entityId}/status`);
};

export const fetchDraft = (entityId: string): Promise<EntityRevision | null> => {
  return request<EntityRevision | null>(`/api/entities/${entityId}/draft`);
};

export const forkDraft = (entityId: string): Promise<EntityRevision> => {
  return request<EntityRevision>(`/api/entities/${entityId}/draft`, {
    method: "POST",
  });
};

export const updateDraft = (
  entityId: string,
  body: {
    properties?: EntityRevisionProperty[];
    links?: Record<string, unknown>[];
    source_nodes?: Record<string, unknown>[];
    computed_properties?: Record<string, unknown>[];
    layout_state?: Record<string, unknown>;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(`/api/entities/${entityId}/draft`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
};

export const discardDraft = (entityId: string): Promise<{ discarded: boolean }> => {
  return request<{ discarded: boolean }>(`/api/entities/${entityId}/draft`, {
    method: "DELETE",
  });
};

export const publishDraft = (
  entityId: string,
  sourceDependencies?: { dependency_type: string; dependency_id: string }[]
): Promise<EntityRevision> => {
  const body: Record<string, unknown> = {};
  if (sourceDependencies !== undefined) {
    body.source_dependencies = sourceDependencies;
  }
  return request<EntityRevision>(`/api/entities/${entityId}/draft/publish`, {
    method: "POST",
    body: JSON.stringify(body),
  });
};

export const fetchRevisions = (entityId: string): Promise<EntityRevision[]> => {
  return request<EntityRevision[]>(`/api/entities/${entityId}/revisions`);
};

export const createInitialRevision = (
  entityId: string,
  body: {
    properties?: EntityRevisionProperty[];
    links?: Record<string, unknown>[];
    source_nodes?: Record<string, unknown>[];
    computed_properties?: Record<string, unknown>[];
    layout_state?: Record<string, unknown>;
    publish?: boolean;
    source_dependencies?: { dependency_type: string; dependency_id: string }[];
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(`/api/entities/${entityId}/revisions`, {
    method: "POST",
    body: JSON.stringify(body),
  });
};
