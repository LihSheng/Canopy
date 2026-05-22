import { test, expect, type Page } from "@playwright/test";

// ── Fixtures ──

/** Mock all API calls the dashboard page depends on. */
async function mockDashboardApis(page: Page) {
  // Auth session — return authenticated user with tenant
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

  // Auto-enter tenant
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

  // Dashboard data
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
        { id: "d3", name: "Marketing", total_spend: 200_000, payroll_spend: 150_000, claims_spend: 50_000, change_pct: 12.0 },
        { id: "d4", name: "Operations", total_spend: 150_000, payroll_spend: 100_000, claims_spend: 50_000, change_pct: 0.5 },
        { id: "d5", name: "HR", total_spend: 50_000, payroll_spend: 40_000, claims_spend: 10_000, change_pct: -1.0 },
      ]),
    });
  });

  await page.route("**/api/dashboard/trends", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { month: "Jan", payroll: 900_000, claims: 180_000, total: 1_080_000 },
        { month: "Feb", payroll: 950_000, claims: 190_000, total: 1_140_000 },
        { month: "Mar", payroll: 1_000_000, claims: 200_000, total: 1_200_000 },
        { month: "Apr", payroll: 980_000, claims: 210_000, total: 1_190_000 },
        { month: "May", payroll: 1_020_000, claims: 190_000, total: 1_210_000 },
        { month: "Jun", payroll: 1_000_000, claims: 200_000, total: 1_200_000 },
      ]),
    });
  });

  await page.route("**/api/dashboard/claim-types", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { type: "Travel", amount: 100_000, count: 50 },
        { type: "Meals", amount: 50_000, count: 30 },
        { type: "Office Supplies", amount: 30_000, count: 20 },
        { type: "Software", amount: 20_000, count: 10 },
      ]),
    });
  });

  await page.route("**/api/anomalies", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high", change_pct: 15 },
        { id: "a2", department_id: "d3", department_name: "Marketing", period: "2024-06", description: "Unusual claims pattern", severity: "medium", change_pct: 12 },
      ]),
    });
  });

  // Refresh status (polled by refresh-widgets)
  await page.route("**/api/refresh/current", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "idle",
        last_refresh: "2024-06-15T10:00:00Z",
        last_attempt: null,
        error_message: null,
      }),
    });
  });
}

/** Mock session as unauthenticated so we can verify redirect behaviour. */
async function mockUnauthenticated(page: Page) {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: false,
        user: null,
        tenant: null,
        tenants: [],
      }),
    });
  });
}

/** Mock all dashboard APIs to return 500 errors. */
async function mockDashboardErrors(page: Page) {
  await page.route("**/api/auth/session", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        authenticated: true,
        user: { id: "1", email: "admin@canopy.dev", display_name: "Admin" },
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
        user: { id: "1", email: "admin@canopy.dev", display_name: "Admin" },
        tenant: { tenant_id: "t1", role: "admin" },
        tenants: [{ tenant_id: "t1", name: "Default", role: "admin" }],
      }),
    });
  });

  // Make dashboard data endpoints fail
  const failPaths = [
    "**/api/dashboard/summary",
    "**/api/departments",
    "**/api/dashboard/trends",
    "**/api/dashboard/claim-types",
    "**/api/anomalies",
  ];
  for (const path of failPaths) {
    await page.route(path, async (route) => {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Internal server error" }),
      });
    });
  }

  await page.route("**/api/refresh/current", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ status: "idle", last_refresh: null, last_attempt: null, error_message: null }),
    });
  });
}

// ── Tests ──

test.describe("Dashboard page", () => {
  test("redirects to login when unauthenticated", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/dashboard");

    // Should redirect to /login with a redirect param
    await page.waitForURL(/\/login/, { timeout: 10000 });
    await expect(page.getByText("Sign in to your account")).toBeVisible();
  });

  test("loads and displays summary data", async ({ page }) => {
    await mockDashboardApis(page);
    await page.goto("/dashboard");

    // Wait for dashboard title to appear
    await expect(page.getByText("Dashboard")).toBeVisible({ timeout: 15000 });

    // Summary card values
    await expect(page.getByText("$1,200,000")).toBeVisible(); // Total Spend
    await expect(page.getByText("$1,000,000")).toBeVisible(); // Payroll Spend
    await expect(page.getByText("$200,000")).toBeVisible();   // Claims Spend
    await expect(page.getByText("2")).toBeVisible();           // Attention Count
  });

  test("displays attention items for anomalies", async ({ page }) => {
    await mockDashboardApis(page);
    await page.goto("/dashboard");

    await expect(page.getByText("Top Attention Items")).toBeVisible({ timeout: 15000 });
    // First anomaly department and description
    await expect(page.getByText("Engineering")).toBeVisible();
    await expect(page.getByText("Payroll spike")).toBeVisible();
    // Second anomaly
    await expect(page.getByText("Marketing")).toBeVisible();
    await expect(page.getByText("Unusual claims pattern")).toBeVisible();
  });

  test("displays top departments", async ({ page }) => {
    await mockDashboardApis(page);
    await page.goto("/dashboard");

    await expect(page.getByText("Top Departments")).toBeVisible({ timeout: 15000 });
    // Department names from mock data
    await expect(page.getByText("Engineering")).toBeVisible();
    await expect(page.getByText("Sales")).toBeVisible();
    await expect(page.getByText("Marketing")).toBeVisible();
    // Spend values
    await expect(page.getByText("$500,000")).toBeVisible();
  });

  test("displays AI summary panel", async ({ page }) => {
    await mockDashboardApis(page);
    await page.goto("/dashboard");

    await expect(page.getByText("AI Summary")).toBeVisible({ timeout: 15000 });
    // AI badge
    await expect(page.getByText("AI")).toBeVisible();
    // Headline
    await expect(page.getByText("Spend overview for 2024-06")).toBeVisible();
  });

  test("shows error state with retry button when APIs fail", async ({ page }) => {
    await mockDashboardErrors(page);
    await page.goto("/dashboard");

    // Should show the error state with the error message and retry button
    await expect(page.getByText("Try again")).toBeVisible({ timeout: 15000 });
    await expect(page.getByText("Internal server error")).toBeVisible();
  });

  test("shows refresh status in the UI", async ({ page }) => {
    await mockDashboardApis(page);
    await page.goto("/dashboard");

    // The refresh timeline panel shows when data was last refreshed
    await expect(page.getByText("Up to date")).toBeVisible({ timeout: 15000 });
  });
});
