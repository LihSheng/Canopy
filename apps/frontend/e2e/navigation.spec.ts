import { test, expect, type Page } from "@playwright/test";

// ── Helpers ──

async function mockAuthenticatedSession(page: Page) {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: { id: "1", email: "admin@canopy.dev", display_name: "Admin User" },
        tenant: { tenant_id: "t1", role: "admin" },
        tenants: [{ tenant_id: "t1", name: "Default", role: "admin" }],
      }),
    });
  });

  await page.route("**/api/auth/switch-tenant", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: { id: "1", email: "admin@canopy.dev", display_name: "Admin User" },
        tenant: { tenant_id: "t1", role: "admin" },
        tenants: [{ tenant_id: "t1", name: "Default", role: "admin" }],
      }),
    });
  });
}

/** Stub all dashboard data APIs so page content renders. */
async function stubDataApis(page: Page) {
  await page.route("**/api/dashboard/summary", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        total_payroll: 1_000_000,
        total_claims: 200_000,
        period: { year: 2024, month: 6 },
        department_count: 5,
        anomaly_count: 2,
        last_updated: "2024-06-15T10:00:00Z",
      }),
    });
  });

  await page.route("**/api/departments", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { id: "d1", name: "Engineering", total_spend: 500_000, payroll_spend: 400_000, claims_spend: 100_000, change_pct: 5.0 },
        { id: "d2", name: "Sales", total_spend: 300_000, payroll_spend: 200_000, claims_spend: 100_000, change_pct: -2.0 },
      ]),
    });
  });

  await page.route("**/api/dashboard/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route("**/api/dashboard/claim-types", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([]),
    });
  });

  await page.route("**/api/anomalies", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high", change_pct: 15 },
      ]),
    });
  });

  await page.route("**/api/refresh/current", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "idle", last_refresh: "2024-06-15T10:00:00Z", last_attempt: null, error_message: null }),
    });
  });

  await page.route("**/api/export/history", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ jobs: [] }),
    });
  });
}

test.describe("Sidebar navigation", () => {
  test.beforeEach(async ({ page }) => {
    await mockAuthenticatedSession(page);
    await stubDataApis(page);
  });

  test("sidebar shows all main nav items", async ({ page }) => {
    // Use desktop viewport so sidebar is visible
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard");

    await expect(page.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Anomalies" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Departments" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Reports" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Data Studio" })).toBeVisible();
  });

  test("clicking Anomalies navigates to anomalies page", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard");

    // Scope to sidebar <aside> to avoid matching dashboard content links
    await page.locator("aside").getByRole("link", { name: "Anomalies" }).click();
    await page.waitForURL("/dashboard/anomalies", { timeout: 10000 });

    // The anomalies page shell renders "Anomalies" as its <h1> heading
    await expect(page.getByRole("heading", { name: "Anomalies" })).toBeVisible();
  });

  test("clicking Departments navigates to departments page", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard");

    await page.locator("aside").getByRole("link", { name: "Departments" }).click();
    await page.waitForURL("/dashboard/departments", { timeout: 10000 });

    await expect(page.getByRole("heading", { name: "Departments" })).toBeVisible();
  });

  test("clicking Reports navigates to reports page", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard");

    await page.locator("aside").getByRole("link", { name: "Reports" }).click();
    await page.waitForURL("/dashboard/reports", { timeout: 10000 });

    await expect(page.getByRole("heading", { name: "Reports" })).toBeVisible();
  });

  test("clicking Dashboard returns to dashboard page", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard/anomalies");
    // Wait for anomalies page heading
    await expect(page.getByRole("heading", { name: "Anomalies" })).toBeVisible({ timeout: 10000 });

    await page.locator("aside").getByRole("link", { name: "Dashboard" }).click();
    await page.waitForURL("/dashboard", { timeout: 10000 });

    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("navigates to profile page", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
    await page.goto("/dashboard");

    await page.getByRole("link", { name: "Profile" }).click();
    await page.waitForURL("/dashboard/profile", { timeout: 10000 });

    await expect(page.getByRole("heading", { name: "Profile" })).toBeVisible();
  });
});
