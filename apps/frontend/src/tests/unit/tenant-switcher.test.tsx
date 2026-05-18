import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { TenantSwitcher } from "@/components/auth/tenant-switcher";
import { switchTenant } from "@/lib/api/auth";
import type { TenantInfo } from "@/lib/api/types";

vi.mock("@/lib/api/auth", () => ({
  switchTenant: vi.fn(),
}));

const mockTenants: TenantInfo[] = [
  { tenant_id: "t1", name: "Alpha Corp", role: "admin" },
  { tenant_id: "t2", name: "Beta Inc", role: "member" },
  { tenant_id: "t3", name: "Gamma LLC", role: "owner" },
];

describe("TenantSwitcher", () => {
  it("renders all tenant options", () => {
    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId={null}
        onTenantSwitch={vi.fn()}
      />
    );

    expect(screen.getByText("Alpha Corp (admin)")).toBeInTheDocument();
    expect(screen.getByText("Beta Inc (member)")).toBeInTheDocument();
    expect(screen.getByText("Gamma LLC (owner)")).toBeInTheDocument();
  });

  it("highlights active tenant", () => {
    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId="t2"
        onTenantSwitch={vi.fn()}
      />
    );

    const activeButton = screen.getByText("Beta Inc (member)");
    expect(activeButton.className).toContain("bg-zinc-900");
    expect(activeButton.className).toContain("text-white");
  });

  it("does not highlight non-active tenants", () => {
    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId="t1"
        onTenantSwitch={vi.fn()}
      />
    );

    const inactive = screen.getByText("Beta Inc (member)");
    expect(inactive.className).not.toContain("bg-zinc-900");
  });

  it("calls switchTenant and onTenantSwitch on selection", async () => {
    vi.mocked(switchTenant).mockResolvedValueOnce({
      authenticated: true,
      user: { id: "u1", email: "test@example.com", display_name: "Test" },
      tenant: { tenant_id: "t1", role: "admin" },
      tenants: mockTenants,
    });

    const onTenantSwitch = vi.fn();

    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId={null}
        onTenantSwitch={onTenantSwitch}
      />
    );

    fireEvent.click(screen.getByText("Alpha Corp (admin)"));

    await waitFor(() => {
      expect(switchTenant).toHaveBeenCalledWith("t1");
      expect(onTenantSwitch).toHaveBeenCalled();
    });
  });

  it("disables buttons while switching", async () => {
    vi.mocked(switchTenant).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                authenticated: true,
                user: {
                  id: "u1",
                  email: "test@example.com",
                  display_name: "Test",
                },
                tenant: { tenant_id: "t2", role: "member" },
                tenants: mockTenants,
              }),
            100
          )
        )
    );

    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId={null}
        onTenantSwitch={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("Beta Inc (member)"));

    const buttons = screen.getAllByRole("button");
    for (const btn of buttons) {
      expect(btn).toBeDisabled();
    }
  });

  it("shows error message on switch failure", async () => {
    vi.mocked(switchTenant).mockRejectedValueOnce(
      new Error("Tenant is suspended")
    );

    render(
      <TenantSwitcher
        tenants={mockTenants}
        activeTenantId={null}
        onTenantSwitch={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("Gamma LLC (owner)"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Tenant is suspended"
      );
    });
  });

  it("renders nothing when tenants list is empty", () => {
    const { container } = render(
      <TenantSwitcher
        tenants={[]}
        activeTenantId={null}
        onTenantSwitch={vi.fn()}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});
