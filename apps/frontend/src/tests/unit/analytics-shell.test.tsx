import { render, screen, fireEvent, within } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { Mock } from "vitest";

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

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  usePathname: () => mockPathname,
  useSearchParams: () => new URLSearchParams(),
}));

import { AnalyticsLayoutProvider } from "@/components/analytics-shell/analytics-layout-context";
import { AnalyticsSidebarItem } from "@/components/analytics-shell/analytics-sidebar-item";
import { AnalyticsSidebarBrand } from "@/components/analytics-shell/analytics-sidebar-brand";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { AnalyticsShell } from "@/components/analytics-shell/analytics-shell";

function Wrapper({ children }: { children: React.ReactNode }) {
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
    expect(screen.getByText("Herd Aggregator")).toBeInTheDocument();
  });

  it("hides brand text when collapsed", () => {
    render(<AnalyticsSidebarBrand collapsed />);
    expect(screen.queryByText("Herd Aggregator")).not.toBeInTheDocument();
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
});

describe("AnalyticsShell - drawer behavior", () => {
  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
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
