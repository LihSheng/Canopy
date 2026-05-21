import type { TenantContextResponse, TenantInfo } from "./types";
import { request } from "./client";

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SessionUser {
  id: string;
  email: string;
  display_name: string;
}

export interface LoginResponse {
  user: SessionUser;
  token: string;
  expires_at: string;
  tenants: TenantInfo[];
}

export interface SessionResponse {
  authenticated: boolean;
  user: SessionUser | null;
  tenant: TenantContextResponse | null;
  tenants: TenantInfo[];
}

export const login = async (payload: LoginPayload): Promise<LoginResponse> => {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export const logout = async (): Promise<void> => {
  await request("/api/auth/logout", { method: "POST" });
}

export const getSession = async (): Promise<SessionResponse> => {
  return request<SessionResponse>("/api/auth/session");
}

export const switchTenant = async (
  tenantId: string
): Promise<SessionResponse> => {
  return request<SessionResponse>("/api/auth/switch-tenant", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId }),
  });
}
