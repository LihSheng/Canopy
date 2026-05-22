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
    await mockUnauthenticated(page);
    await mockLoginSuccess(page);
    await page.goto("/login");

    await page.getByLabel("Email").fill("admin@canopy.dev");
    await page.getByLabel("Password").fill("correct-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    // After successful login the app redirects to /dashboard
    await page.waitForURL("/dashboard", { timeout: 10000 });
    await expect(page.getByText("Dashboard")).toBeVisible();
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
    const btn = page.getByRole("button", { name: "Sign in" });
    await btn.click();

    // Button should show "Signing in..." and be disabled
    await expect(page.getByText("Signing in...")).toBeVisible();
    await expect(btn).toBeDisabled();
  });
});
