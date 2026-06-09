import { request } from "./client";
import type {
  ComputedProperty,
  EntityLink,
  ObjectType,
  SchemaColumn,
  PropertyMapping,
  SemanticMapping,
  SourceNode,
  ValidationResult,
} from "./types";

// ─── Object Types ───

export const fetchObjectTypes = (): Promise<ObjectType[]> => {
  return request<ObjectType[]>("/api/semantic/object-types");
};

export const createObjectType = (data: {
  object_type_key: string;
  display_name: string;
  description?: string;
}): Promise<ObjectType> => {
  return request<ObjectType>("/api/semantic/object-types", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

// ─── Entity Creation Helper (Palantir-style flow) ───

export const createEntity = (data: {
  display_name: string;
  description?: string;
  plural_name?: string;
  icon?: string;
  groups?: string[];
}): Promise<ObjectType> => {
  return request<ObjectType>("/api/semantic/create-entity", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const fetchObjectType = (id: string): Promise<ObjectType> => {
  return request<ObjectType>(`/api/semantic/object-types/${id}`);
};

export const updateObjectType = (
  id: string,
  data: { display_name?: string; description?: string }
): Promise<ObjectType> => {
  return request<ObjectType>(`/api/semantic/object-types/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
};

// ─── Object Type Primary Key Resolution ───

export type ResolvedPrimaryKey = {
  property_name: string | null;
  semantic_type: string | null;
};

export const fetchObjectTypePrimaryKey = (
  id: string
): Promise<ResolvedPrimaryKey> => {
  return request<ResolvedPrimaryKey>(
    `/api/semantic/object-types/${id}/primary-key`
  );
};

// ─── Schema ───

export const fetchDatasetVersionSchema = (
  datasetId: string,
  versionId: string
): Promise<SchemaColumn[]> => {
  return request<SchemaColumn[]>(
    `/api/semantic/datasets/${datasetId}/versions/${versionId}/schema`
  );
};

// ─── Mappings ───

export const fetchMapping = (
  datasetId: string,
  versionId: string
): Promise<SemanticMapping | null> => {
  return request<SemanticMapping | null>(
    `/api/semantic/datasets/${datasetId}/versions/${versionId}/mapping`
  );
};

export const createMapping = (
  datasetId: string,
  versionId: string,
  data: {
    object_type_id: string;
    properties: PropertyMapping[];
    links?: EntityLink[];
    source_nodes?: SourceNode[];
    computed_properties?: ComputedProperty[];
    layout_state?: Record<string, unknown>;
  }
): Promise<SemanticMapping> => {
  return request<SemanticMapping>(
    `/api/semantic/datasets/${datasetId}/versions/${versionId}/mapping`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
};

export const updateMapping = (
  datasetId: string,
  versionId: string,
  data: {
    object_type_id: string;
    properties: PropertyMapping[];
    links?: EntityLink[];
    source_nodes?: SourceNode[];
    computed_properties?: ComputedProperty[];
    layout_state?: Record<string, unknown>;
  }
): Promise<SemanticMapping> => {
  return request<SemanticMapping>(
    `/api/semantic/datasets/${datasetId}/versions/${versionId}/mapping`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    }
  );
};

export const validateMapping = (
  datasetId: string,
  versionId: string,
  data: {
    object_type_id: string;
    properties: PropertyMapping[];
    links?: EntityLink[];
    computed_properties?: ComputedProperty[];
    source_nodes?: SourceNode[];
  }
): Promise<ValidationResult> => {
  return request<ValidationResult>(
    `/api/semantic/datasets/${datasetId}/versions/${versionId}/mapping/validate`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
};

// ─── Aggregation ───

export type AggregationType = "count" | "sum" | "avg" | "min" | "max" | "count_distinct";

export type AggregationRequest = {
  object_type_id: string;
  dimension: string;
  metric: {
    property: string;
    type: AggregationType;
  };
  filter_expression?: Record<string, unknown> | null;
};

export type AggregationBucket = {
  dimension_value: string;
  metric_value: number;
};

export type AggregationResponse = {
  object_type: string;
  results: AggregationBucket[];
  truncated: boolean;
};

export const aggregateObjectSet = (
  objectTypeId: string,
  data: AggregationRequest
): Promise<AggregationResponse> => {
  return request<AggregationResponse>(
    `/api/semantic/object-types/${objectTypeId}/aggregate`,
    {
      method: "POST",
      body: JSON.stringify(data),
    }
  );
};

