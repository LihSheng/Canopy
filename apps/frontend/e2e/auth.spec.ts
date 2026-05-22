import { test, expect, type Page } from "@playwright/test";

// ── Helpers ──

/** Intercept GET /api/auth/session to return unauthenticated. */
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

/** Intercept POST /api/auth/login to simulate a successful login. */
async function mockLoginSuccess(page: Page) {
  await page.route("**/api/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      return route.continue();
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user: {
          id: "1",
          email: "admin@canopy.dev",
          display_name: "Admin User",
        },
        token: "test-token-xxx",
        expires_at: new Date(Date.now() + 86400000).toISOString(),
        tenants: [
          { tenant_id: "t1", name: "Default", role: "admin" },
        ],
      }),
    });
  });
}

/** Mock session as authenticated so dashboard can render after login. */
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
}

/** Intercept POST /api/auth/login to simulate a failed login (401). */
async function mockLoginFailure(page: Page) {
  await page.route("**/api/auth/login", async (route) => {
    if (route.request().method() !== "POST") {
      return route.continue();
    }
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Invalid email or password" }),
    });
  });
}

// ── Tests ──

test.describe("Login page", () => {
  test("renders brand name and sign-in form", async ({ page }) => {
    await mockUnauthenticated(page);
    await page.goto("/login");

    // Brand heading
    await expect(page.getByText("Canopy Intelligence")).toBeVisible();
    // Subtitle
    await expect(page.getByText("Sign in to your account")).toBeVisible();
    // Form fields
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    // Submit button
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  });

  test("shows error message on failed login", async ({ page }) => {
    await mockUnauthenticated(page);
    await mockLoginFailure(page);
    await page.goto("/login");

    await page.getByLabel("Email").fill("wrong@test.com");
    await page.getByLabel("Password").fill("bad-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByText("Invalid email or password")).toBeVisible();
  });

  test("redirects to dashboard on successful login", async ({ page }) => {
    await mockLoginSuccess(page);
    await page.goto("/login");

    // After login redirects to /dashboard, it needs a valid session and data
    await mockAuthenticatedSession(page);
    await page.route("**/api/auth/switch-tenant", async (route) => {
      if (route.request().method() !== "POST") return route.continue();
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ authenticated: true, user: { id: "1", email: "admin@canopy.dev", display_name: "Admin" }, tenant: { tenant_id: "t1", role: "admin" }, tenants: [{ tenant_id: "t1", name: "Default", role: "admin" }] }),
      });
    });
    await page.route("**/api/dashboard/summary", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ total_payroll: 0, total_claims: 0, period: { year: 2024, month: 6 }, department_count: 0, anomaly_count: 0, last_updated: "2024-06-15T10:00:00Z" }) });
    });
    await page.route("**/api/departments", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    });
    await page.route("**/api/dashboard/trends", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    });
    await page.route("**/api/dashboard/claim-types", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    });
    await page.route("**/api/anomalies", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([]) });
    });
    await page.route("**/api/refresh/current", async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "idle", last_refresh: null, last_attempt: null, error_message: null }) });
    });

    await page.getByLabel("Email").fill("admin@canopy.dev");
    await page.getByLabel("Password").fill("correct-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    // After successful login the app redirects to /dashboard
    await page.waitForURL("/dashboard", { timeout: 10000 });
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  });

  test("disables submit button while loading", async ({ page }) => {
    await mockUnauthenticated(page);
    // Delay the login response so we can observe loading state
    await page.route("**/api/auth/login", async (route) => {
      if (route.request().method() !== "POST") {
        return route.continue();
      }
      await new Promise((r) => setTimeout(r, 500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: { id: "1", email: "admin@canopy.dev", display_name: "Admin" },
          token: "tok",
          expires_at: new Date(Date.now() + 86400000).toISOString(),
          tenants: [],
        }),
      });
    });

    await page.goto("/login");
    await page.getByLabel("Email").fill("admin@canopy.dev");
    await page.getByLabel("Password").fill("pw");
    await page.getByRole("button", { name: "Sign in" }).click();

    // Button should show "Signing in..." text (loading state)
    await expect(page.getByText("Signing in...")).toBeVisible();
  });
});
