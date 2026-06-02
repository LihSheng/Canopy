import { request } from "./client";

export interface FeatureFlag {
  flag_key: string;
  description: string;
  enabled: boolean;
}

/** Fetch the map of flag_key -> enabled for all users (authenticated). */
export async function fetchEnabledFlags(): Promise<Record<string, boolean>> {
  return request<Record<string, boolean>>("/api/feature-flags");
}

/** Admin: list all feature flags with descriptions. */
export async function fetchAllFlags(): Promise<FeatureFlag[]> {
  return request<FeatureFlag[]>("/api/admin/feature-flags");
}

/** Admin: toggle a feature flag on or off. */
export async function toggleFlag(
  flagKey: string,
  enabled: boolean
): Promise<FeatureFlag> {
  return request<FeatureFlag>(`/api/admin/feature-flags/${flagKey}`, {
    method: "PUT",
    body: JSON.stringify({ enabled }),
  });
}
