import { describe, expect, it, vi, beforeEach } from "vitest";
import { request } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  request: vi.fn(),
  API_BASE: "http://localhost:8005",
}));

import { login, logout, getSession, switchTenant } from "@/lib/api/auth";

const mockRequest = vi.mocked(request);

describe("auth API", () => {
  beforeEach(() => {
    mockRequest.mockReset();
  });

  describe("login", () => {
    it("calls /api/auth/login with POST and payload", async () => {
      mockRequest.mockResolvedValue({
        user: { id: "1", email: "a@b.com", display_name: "A" },
        token: "tok",
        expires_at: "2026-06-01T00:00:00Z",
        tenants: [],
      });

      const result = await login({ email: "a@b.com", password: "secret" });

      expect(mockRequest).toHaveBeenCalledWith("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email: "a@b.com", password: "secret" }),
      });
      expect(result.user.email).toBe("a@b.com");
    });
  });

  describe("logout", () => {
    it("calls /api/auth/logout with POST", async () => {
      mockRequest.mockResolvedValue(undefined);
      await logout();
      expect(mockRequest).toHaveBeenCalledWith("/api/auth/logout", {
        method: "POST",
      });
    });
  });

  describe("getSession", () => {
    it("calls /api/auth/session", async () => {
      mockRequest.mockResolvedValue({
        authenticated: true,
        user: { id: "1", email: "a@b.com", display_name: "A" },
        tenant: null,
        tenants: [],
      });

      const result = await getSession();
      expect(mockRequest).toHaveBeenCalledWith("/api/auth/session");
      expect(result.authenticated).toBe(true);
    });
  });

  describe("switchTenant", () => {
    it("calls /api/auth/switch-tenant with POST and tenant_id", async () => {
      mockRequest.mockResolvedValue({
        authenticated: true,
        user: { id: "1", email: "a@b.com", display_name: "A" },
        tenant: { tenant_id: "t2", role: "admin" },
        tenants: [],
      });

      const result = await switchTenant("t2");
      expect(mockRequest).toHaveBeenCalledWith("/api/auth/switch-tenant", {
        method: "POST",
        body: JSON.stringify({ tenant_id: "t2" }),
      });
      expect(result.tenant?.tenant_id).toBe("t2");
    });
  });
});
