import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/data-source", () => ({
  fetchConnections: vi.fn(),
  fetchDatasets: vi.fn().mockResolvedValue([]),
  fetchRuns: vi.fn().mockResolvedValue([]),
  fetchConnectionDependencies: vi.fn(),
  deleteConnection: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import ConnectionsHomeContent from "@/app/dashboard/connections/connections-home-content";
import * as api from "@/lib/api/data-source";

describe("Connections home", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders connection rows and allows deleting an unused connection", async () => {
    vi.mocked(api.fetchConnections).mockResolvedValue([
      {
        id: "conn-1",
        project_id: "proj-1",
        source_type: "static_file",
        name: "Dummy File",
        status: "active",
        config_json: {},
        created_at: "2026-05-18T00:00:00Z",
        updated_at: "2026-05-18T00:00:00Z",
      },
    ]);
    vi.mocked(api.fetchConnectionDependencies).mockResolvedValue({
      connection_id: "conn-1",
      active_dataset_count: 0,
      active_run_count: 0,
      can_delete: true,
    });
    vi.mocked(api.deleteConnection).mockResolvedValue({ deleted: true, id: "conn-1" });
    const confirm_spy = vi.spyOn(window, "confirm").mockReturnValue(true);

    render(<ConnectionsHomeContent />);

    await waitFor(() => {
      expect(screen.getByText("Dummy File")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(api.fetchConnectionDependencies).toHaveBeenCalledWith("conn-1");
      expect(api.deleteConnection).toHaveBeenCalledWith("conn-1");
    });

    expect(confirm_spy).toHaveBeenCalledWith('Delete connection "Dummy File"?');
    confirm_spy.mockRestore();
  });

  it("blocks delete when the connection still has dependencies", async () => {
    vi.mocked(api.fetchConnections).mockResolvedValue([
      {
        id: "conn-2",
        project_id: "proj-1",
        source_type: "static_file",
        name: "Used File",
        status: "active",
        config_json: {},
        created_at: "2026-05-18T00:00:00Z",
        updated_at: "2026-05-18T00:00:00Z",
      },
    ]);
    vi.mocked(api.fetchConnectionDependencies).mockResolvedValue({
      connection_id: "conn-2",
      active_dataset_count: 1,
      active_run_count: 0,
      can_delete: false,
    });

    render(<ConnectionsHomeContent />);

    await waitFor(() => {
      expect(screen.getByText("Used File")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Cannot delete "Used File" yet/i),
      ).toBeInTheDocument();
    });
    expect(api.deleteConnection).not.toHaveBeenCalled();
  });
});
