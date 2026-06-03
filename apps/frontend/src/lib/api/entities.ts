import { request } from "./client";
import type {
  EntityRegistryItem,
  EntityDetail,
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
