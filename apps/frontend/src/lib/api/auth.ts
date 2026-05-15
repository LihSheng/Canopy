const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

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
}

export interface SessionResponse {
  authenticated: boolean;
  user: SessionUser | null;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }

  return res.json();
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
