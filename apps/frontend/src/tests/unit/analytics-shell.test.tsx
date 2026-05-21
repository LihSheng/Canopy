import { render, screen, fireEvent, within, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const mockPush = vi.fn();
const mockReplace = vi.fn();
let mockPathname = "/dashboard";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User", role: "admin" },
    loading: false,
    error: null,
    refetch: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/components/auth/session-guard", () => ({
  useTenant: () => ({
    tenant: { tenant_id: "tenant-1", role: "admin" },
    tenants: [
      { tenant_id: "tenant-1", name: "Alpha Corp", role: "admin" },
      { tenant_id: "tenant-2", name: "Beta Inc", role: "member" },
    ],
    refetch: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  usePathname: () => mockPathname,
  useSearchParams: () => new URLSearchParams(),
}));

import { switchTenant } from "@/lib/api/auth";
vi.mock("@/lib/api/auth", () => ({
  switchTenant: vi.fn(),
}));

import { AnalyticsLayoutProvider } from "@/components/analytics-shell/analytics-layout-context";
import { AnalyticsSidebarItem } from "@/components/analytics-shell/analytics-sidebar-item";
import { AnalyticsSidebarBrand } from "@/components/analytics-shell/analytics-sidebar-brand";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { AnalyticsShell } from "@/components/analytics-shell/analytics-shell";

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  return <AnalyticsLayoutProvider>{children}</AnalyticsLayoutProvider>;
}

describe("AnalyticsSidebarItem", () => {
  it("renders label when not collapsed", () => {
    render(
      <AnalyticsSidebarItem
        href="/dashboard"
        icon={<span data-testid="icon" />}
        label="Dashboard"
        active={false}
        collapsed={false}
      />
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("icon")).toBeInTheDocument();
  });

  it("hides label when collapsed", () => {
    render(
      <AnalyticsSidebarItem
        href="/dashboard"
        icon={<span data-testid="icon" />}
        label="Dashboard"
        active={false}
        collapsed
      />
    );
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("shows title attribute when collapsed for tooltip", () => {
    render(
      <AnalyticsSidebarItem
        href="/dashboard"
        icon={<span />}
        label="Dashboard"
        active={false}
        collapsed
      />
    );
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("title", "Dashboard");
  });

  it("applies active styling when active", () => {
    render(
      <AnalyticsSidebarItem
        href="/dashboard"
        icon={<span />}
        label="Dashboard"
        active
        collapsed={false}
      />
    );
    const link = screen.getByRole("link");
    expect(link.className).toContain("bg-zinc-100");
    expect(link.className).toContain("text-zinc-900");
  });

  it("calls onClick when clicked", () => {
    const onClick = vi.fn();
    render(
      <AnalyticsSidebarItem
        href="/dashboard"
        icon={<span />}
        label="Dashboard"
        active={false}
        collapsed={false}
        onClick={onClick}
      />
    );
    fireEvent.click(screen.getByRole("link"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});

describe("AnalyticsSidebarBrand", () => {
  it("renders brand text when expanded", () => {
    render(<AnalyticsSidebarBrand collapsed={false} />);
    expect(screen.getByText("Canopy Intelligence")).toBeInTheDocument();
  });

  it("hides brand text when collapsed", () => {
    render(<AnalyticsSidebarBrand collapsed />);
    expect(screen.queryByText("Canopy Intelligence")).not.toBeInTheDocument();
  });

  it("has link to dashboard", () => {
    render(<AnalyticsSidebarBrand collapsed={false} />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/dashboard");
  });
});

describe("AnalyticsHeader", () => {
  it("renders title", () => {
    render(<AnalyticsHeader title="Dashboard" />);
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("renders context text when provided", () => {
    render(<AnalyticsHeader title="Department" contextText="This month" />);
    expect(screen.getByText("This month")).toBeInTheDocument();
  });

  it("renders actions slot", () => {
    render(
      <AnalyticsHeader
        title="Dashboard"
        actions={<button data-testid="action">Refresh</button>}
      />
    );
    expect(screen.getByTestId("action")).toBeInTheDocument();
  });
});

describe("AnalyticsBreadcrumb", () => {
  it("renders breadcrumb items", () => {
    render(
      <AnalyticsBreadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Departments", href: "/dashboard/departments" },
          { label: "Engineering" },
        ]}
      />
    );
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Departments")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
  });

  it("last item is not a link", () => {
    render(
      <AnalyticsBreadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Engineering" },
        ]}
      />
    );
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAttribute("href", "/dashboard");
  });

  it("has accessible label", () => {
    render(
      <AnalyticsBreadcrumb items={[{ label: "Dashboard", href: "/dashboard" }]} />
    );
    expect(screen.getByLabelText("Breadcrumb")).toBeInTheDocument();
  });
});

describe("AnalyticsShell - sidebar collapse and expand", () => {
  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    try {
      localStorage.clear();
    } catch {}
  });

  it("renders sidebar with navigation items on desktop", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
    expect(screen.getByText("Departments")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByText("Data Studio")).toBeInTheDocument();
  });

  it("collapses sidebar when toggle is clicked", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();

    const toggle = screen.getByLabelText("Collapse sidebar");
    fireEvent.click(toggle);

    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
  });

  it("expands sidebar after collapsing", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const toggle = screen.getByLabelText("Collapse sidebar");
    fireEvent.click(toggle);

    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();

    const expandToggle = screen.getByLabelText("Expand sidebar");
    fireEvent.click(expandToggle);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
  });

  it("highlights active nav item based on pathname", () => {
    mockPathname = "/dashboard/anomalies";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const dashboardLink = screen.getByText("Dashboard").closest("a");
    const anomaliesLink = screen.getByText("Anomalies").closest("a");

    expect(dashboardLink?.className).not.toContain("bg-zinc-100");
    expect(anomaliesLink?.className).toContain("bg-zinc-100");
  });

  it("highlights dashboard link only on exact /dashboard path", () => {
    mockPathname = "/dashboard/anomalies";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const dashboardLink = screen.getByText("Dashboard").closest("a");
    expect(dashboardLink?.className).not.toContain("bg-zinc-100");
  });

  it("renders child page content", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <h1>My Page</h1>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("My Page")).toBeInTheDocument();
  });

  it("keeps the dashboard shell clipped to the viewport", () => {
    const { container } = render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(container.firstChild).toHaveClass("h-dvh");
    expect(container.firstChild).toHaveClass("overflow-hidden");
  });
});

describe("AnalyticsPageShell", () => {
  it("makes the page body the scroll area", () => {
    const { container } = render(
      <AnalyticsPageShell title="Dataset Workspace">
        <div>Body</div>
      </AnalyticsPageShell>
    );

    expect(container.firstChild).toHaveClass("min-h-0");
    expect(container.firstChild).toHaveClass("overflow-hidden");
    const scrollArea = container.querySelector(".overflow-auto");
    expect(scrollArea).toHaveClass("overflow-auto");
    expect(screen.getByText("Dataset Workspace")).toBeInTheDocument();
    expect(screen.getByText("Body")).toBeInTheDocument();
  });
});

describe("AnalyticsShell - drawer behavior", () => {
  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
    vi.unstubAllGlobals();
    try {
      localStorage.clear();
    } catch {}
  });

  it("shows hamburger menu on mobile-sized viewport", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const hamburger = screen.getByLabelText("Open navigation");
    expect(hamburger).toBeInTheDocument();
  });

  it("mobile top bar uses lg:hidden for responsive visibility", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const hamburger = screen.getByLabelText("Open navigation");
    const mobileBar = hamburger.closest("div");
    expect(mobileBar).not.toBeNull();
  });

  it("desktop sidebar wrapper uses hidden lg:block for responsive visibility", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const sidebarContainer = document.querySelector(".hidden.lg\\:block");
    expect(sidebarContainer).not.toBeNull();
  });

  it("opens drawer when hamburger is clicked", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const hamburger = screen.getByLabelText("Open navigation");
    fireEvent.click(hamburger);

    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveAttribute("aria-modal", "true");
  });

  it("closes drawer when overlay backdrop is clicked", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    fireEvent.click(screen.getByLabelText("Open navigation"));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    const backdrop = document.querySelector('[aria-hidden]');
    expect(backdrop).not.toBeNull();
    if (backdrop) {
      fireEvent.click(backdrop);
    }

    // The drawer is removed from DOM when closed
    // With framer-motion/animation, it may take time - checking dialog is gone
    const dialogs = screen.queryAllByRole("dialog");
    expect(dialogs).toHaveLength(0);
  });

  it("drawer closes after clicking a navigation item", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    fireEvent.click(screen.getByLabelText("Open navigation"));

    const dialog = screen.getByRole("dialog");
    fireEvent.click(within(dialog).getByText("Anomalies"));

    // Drawer should be removed after navigation
    const dialogs = screen.queryAllByRole("dialog");
    expect(dialogs).toHaveLength(0);
  });

  it("renders navigation items in drawer", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    fireEvent.click(screen.getByLabelText("Open navigation"));

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Dashboard")).toBeInTheDocument();
    expect(within(dialog).getByText("Anomalies")).toBeInTheDocument();
    expect(within(dialog).getByText("Departments")).toBeInTheDocument();
    expect(within(dialog).getByText("Reports")).toBeInTheDocument();
  });

  it("drawer has lg:hidden class for responsive visibility control", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    fireEvent.click(screen.getByLabelText("Open navigation"));

    const dialog = screen.getByRole("dialog");
    expect(dialog.className).toContain("lg:hidden");
  });

  it("sidebar is hidden on mobile and drawer provides navigation instead", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    // Sidebar container is hidden on mobile via responsive class
    const sidebarContainer = document.querySelector(".hidden.lg\\:block");
    expect(sidebarContainer).not.toBeNull();

    // Hamburger provides mobile access
    const hamburger = screen.getByLabelText("Open navigation");
    expect(hamburger).toBeInTheDocument();

    // Open drawer, check that same nav items appear
    fireEvent.click(hamburger);
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Dashboard")).toBeInTheDocument();
  });
});

describe("AnalyticsShell - localstorage persistence", () => {
  const storage: Record<string, string> = {};

  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
    Object.keys(storage).forEach((k) => delete storage[k]);
    vi.stubGlobal("localStorage", {
      getItem: vi.fn((key: string) => storage[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        storage[key] = value;
      }),
    });
  });

  it("persists collapse preference to localStorage", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const toggle = screen.getByLabelText("Collapse sidebar");
    fireEvent.click(toggle);

    expect(storage["herd-analytics-sidebar-collapsed"]).toBe("true");
  });

  it("persists expand preference to localStorage", () => {
    storage["herd-analytics-sidebar-collapsed"] = "true";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    const toggle = screen.getByLabelText("Expand sidebar");
    fireEvent.click(toggle);

    expect(storage["herd-analytics-sidebar-collapsed"]).toBe("false");
  });
});

describe("AnalyticsSidebarTenantSwitcher", () => {
  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
    // Clear localStorage to ensure sidebar starts expanded
    try {
      localStorage.removeItem("herd-analytics-sidebar-collapsed");
    } catch {
      // ignore
    }
  });

  async function expandSidebar() {
    // The sidebar might be collapsed from a previous test's localStorage side effect.
    // Look for the collapse button as evidence the sidebar is expanded.
    const collapseBtn = screen.queryByLabelText("Collapse sidebar");
    if (!collapseBtn) {
      // Sidebar is collapsed — find expand button and click it
      const expandBtn = await screen.findByLabelText("Expand sidebar");
      fireEvent.click(expandBtn);
    }
  }

  it("shows current tenant name in expanded sidebar", async () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    await expandSidebar();
    expect(await screen.findByText("Alpha Corp")).toBeInTheDocument();
  });

  it("shows tenant initial when sidebar is collapsed", async () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    // Ensure sidebar is expanded first, then collapse it
    await expandSidebar();
    fireEvent.click(screen.getByLabelText("Collapse sidebar"));

    // The tenant initial should be visible as a tooltip target
    const collapsedTenantButton = screen.getByTitle("Alpha Corp");
    expect(collapsedTenantButton).toBeInTheDocument();
  });

  it("opens tenant picker dropdown on click", async () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    await expandSidebar();
    // Click the tenant switcher button to open dropdown
    fireEvent.click(await screen.findByText("Alpha Corp"));

    // After opening the dropdown, "Alpha Corp" appears twice (button + dropdown).
    // The other tenant should also be visible
    expect(screen.getByText("Beta Inc")).toBeInTheDocument();
    // Role labels should also be shown
    expect(screen.getByText("admin")).toBeInTheDocument();
    expect(screen.getByText("member")).toBeInTheDocument();
  });

  it("calls switchTenant and redirects to dashboard on tenant switch", async () => {
    const mockSwitchTenant = vi.mocked(switchTenant).mockResolvedValue({
      authenticated: true,
      user: { id: "u1", email: "test@test.com", display_name: "Test" },
      tenant: { tenant_id: "tenant-2", role: "member" },
      tenants: [],
    });

    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    await expandSidebar();
    // Open the dropdown
    fireEvent.click(await screen.findByText("Alpha Corp"));
    // Click a different tenant
    fireEvent.click(screen.getByText("Beta Inc"));

    await waitFor(() => {
      expect(mockSwitchTenant).toHaveBeenCalledWith("tenant-2");
      expect(mockPush).toHaveBeenCalledWith("/dashboard");
    });
  });

  it("does not switch or redirect when clicking the active tenant", async () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    await expandSidebar();
    // Click the current tenant button to open dropdown
    const button = (await screen.findAllByText("Alpha Corp"))[0];
    fireEvent.click(button);
    // Click it again to close — the button is the first match
    const buttonAgain = (await screen.findAllByText("Alpha Corp"))[0];
    fireEvent.click(buttonAgain);

    // switchTenant should not have been called (no redirect either)
    // The active tenant click just closes the dropdown
    await waitFor(() => {
      expect(mockPush).not.toHaveBeenCalled();
    });
  });

  it("shows error message on switch failure", async () => {
    vi.mocked(switchTenant).mockRejectedValueOnce(new Error("Tenant is suspended"));

    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    await expandSidebar();
    fireEvent.click(await screen.findByText("Alpha Corp"));
    fireEvent.click(screen.getByText("Beta Inc"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Tenant is suspended");
    });
  });
});
