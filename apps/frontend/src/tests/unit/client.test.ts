import { describe, expect, it, vi, beforeEach } from "vitest";
import { request, API_BASE } from "@/lib/api/client";

describe("request", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("makes a GET request and returns parsed JSON on success", async () => {
    const data = { foo: "bar" };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(data),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await request("/api/test");
    expect(result).toEqual(data);
    expect(mockFetch).toHaveBeenCalledWith(`${API_BASE}/api/test`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
  });

  it("includes custom headers and method", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    await request("/api/data", {
      method: "POST",
      headers: { Authorization: "Bearer tok" },
      body: JSON.stringify({ key: "val" }),
    });

    expect(mockFetch).toHaveBeenCalledWith(`${API_BASE}/api/data`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer tok",
      },
      body: JSON.stringify({ key: "val" }),
    });
  });

  it("omits Content-Type when body is FormData", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    const form = new FormData();
    form.append("file", new Blob(["abc"]), "test.csv");

    await request("/api/upload", { method: "POST", body: form });

    const callHeaders = mockFetch.mock.calls[0][1].headers;
    // FormData path leaves headers undefined so browser auto-sets Content-Type with boundary
    expect(callHeaders).toBeUndefined();
    expect(mockFetch).toHaveBeenCalledWith(
      `${API_BASE}/api/upload`,
      expect.objectContaining({
        method: "POST",
        credentials: "include",
        body: form,
      }),
    );
  });

  it("throws on non-ok response with detail from body", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "Bad request" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(request("/api/test")).rejects.toThrow("Bad request");
  });

  it("throws fallback message when response body has no detail", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(request("/api/test")).rejects.toThrow("HTTP 500");
  });

  it("throws fallback message when json parsing fails on error", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 503,
      json: () => Promise.reject(new Error("parse error")),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(request("/api/test")).rejects.toThrow("Request failed");
  });
});
