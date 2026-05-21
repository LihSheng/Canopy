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

export async function login(payload: LoginPayload): Promise<LoginResponse> {
  return request<LoginResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function logout(): Promise<void> {
  await request("/api/auth/logout", { method: "POST" });
}

export async function getSession(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/auth/session");
}

export async function switchTenant(
  tenantId: string
): Promise<SessionResponse> {
  return request<SessionResponse>("/api/auth/switch-tenant", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId }),
  });
}
