import { request } from "./client";
import type {
  EntityRegistryItem,
  EntityDetail,
  EntityRevision,
  EntityStatus,
  EntityRevisionProperty,
  SourceBinding,
  EntityComputedPropertyDetail,
  EntityLinkDetail,
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

export const fetchRevision = (
  entityId: string,
  revisionId: string
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/revisions/${revisionId}`
  );
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

// ─── Property CRUD (within draft) ───

export const addProperty = (
  entityId: string,
  body: {
    property_key: string;
    display_name: string;
    semantic_type?: string;
    is_required?: boolean;
    is_primary_key?: boolean;
    sort_order?: number;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(`/api/entities/${entityId}/draft/properties`, {
    method: "POST",
    body: JSON.stringify(body),
  });
};

export const updateProperty = (
  entityId: string,
  propertyId: string,
  body: {
    property_key?: string;
    display_name?: string;
    semantic_type?: string;
    is_required?: boolean;
    is_primary_key?: boolean;
    sort_order?: number;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/properties/${propertyId}`,
    {
      method: "PUT",
      body: JSON.stringify(body),
    }
  );
};

export const removeProperty = (
  entityId: string,
  propertyId: string
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/properties/${propertyId}`,
    { method: "DELETE" }
  );
};

export const reorderProperties = (
  entityId: string,
  propertyIds: string[]
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/properties/reorder`,
    {
      method: "PUT",
      body: JSON.stringify({ property_ids: propertyIds }),
    }
  );
};

// ─── Source Bindings ───

export const setSourceBindings = (
  entityId: string,
  bindings: SourceBinding[]
): Promise<EntityRevision> => {
  return request<EntityRevision>(`/api/entities/${entityId}/draft/bindings`, {
    method: "PUT",
    body: JSON.stringify({ bindings }),
  });
};

export const fetchSourceBindings = (
  entityId: string
): Promise<SourceBinding[]> => {
  return request<SourceBinding[]>(`/api/entities/${entityId}/draft/bindings`);
};

export const fetchBrokenBindings = (
  entityId: string
): Promise<SourceBinding[]> => {
  return request<SourceBinding[]>(
    `/api/entities/${entityId}/draft/bindings/broken`
  );
};

// ─── Dataset-Entity Association ───

export const fetchEntityByDataset = (
  datasetId: string
): Promise<EntityDetail | null> => {
  return request<EntityDetail | null>(
    `/api/entities/by-dataset/${datasetId}`
  );
};

// ─── Revert ───

export const revertToRevision = (
  entityId: string,
  revisionId: string
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/revert/${revisionId}`,
    { method: "POST" }
  );
};

// ─── Computed Property CRUD (within draft) ───

export const addComputedProperty = (
  entityId: string,
  body: {
    property_key: string;
    display_name: string;
    formula: string;
    formula_type?: string;
    output_type?: string;
    sort_order?: number;
    is_active?: boolean;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/computed-properties`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
};

export const updateComputedProperty = (
  entityId: string,
  computedPropertyId: string,
  body: {
    property_key?: string;
    display_name?: string;
    formula?: string;
    formula_type?: string;
    output_type?: string;
    sort_order?: number;
    is_active?: boolean;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/computed-properties/${computedPropertyId}`,
    {
      method: "PUT",
      body: JSON.stringify(body),
    }
  );
};

export const removeComputedProperty = (
  entityId: string,
  computedPropertyId: string
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/computed-properties/${computedPropertyId}`,
    { method: "DELETE" }
  );
};

export const listComputedProperties = (
  entityId: string
): Promise<EntityComputedPropertyDetail[]> => {
  return request<EntityComputedPropertyDetail[]>(
    `/api/entities/${entityId}/draft/computed-properties`
  );
};

// ─── Link CRUD (within draft) ───

export const addLink = (
  entityId: string,
  body: {
    link_id: string;
    display_name: string;
    source_property_key: string;
    target_entity_id: string;
    target_property_key: string;
    cardinality: string;
    is_optional?: boolean;
    is_active?: boolean;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/links`,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
};

export const updateLink = (
  entityId: string,
  linkId: string,
  body: {
    display_name?: string;
    source_property_key?: string;
    target_entity_id?: string;
    target_property_key?: string;
    cardinality?: string;
    is_optional?: boolean;
    is_active?: boolean;
  }
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/links/${linkId}`,
    {
      method: "PUT",
      body: JSON.stringify(body),
    }
  );
};

export const removeLink = (
  entityId: string,
  linkId: string
): Promise<EntityRevision> => {
  return request<EntityRevision>(
    `/api/entities/${entityId}/draft/links/${linkId}`,
    { method: "DELETE" }
  );
};

export const listLinks = (
  entityId: string
): Promise<EntityLinkDetail[]> => {
  return request<EntityLinkDetail[]>(
    `/api/entities/${entityId}/draft/links`
  );
};

// ─── Compute/Eval ───

export const evaluateFormula = (
  entityId: string,
  formula: string,
  sampleRow?: Record<string, unknown>
): Promise<{ result: unknown; errors: string[]; warnings: string[] }> => {
  return request<{ result: unknown; errors: string[]; warnings: string[] }>(
    `/api/entities/${entityId}/computed-properties/evaluate`,
    {
      method: "POST",
      body: JSON.stringify({ formula, sample_row: sampleRow || {} }),
    }
  );
};
