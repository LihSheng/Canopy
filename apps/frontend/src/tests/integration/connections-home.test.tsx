import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

    render(<ConnectionsHomeContent />);

    await waitFor(() => {
      expect(screen.getByText("Dummy File")).toBeInTheDocument();
    });

    // Click the row delete button
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    // Confirm dialog should appear
    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText('Delete connection "Dummy File"?'),
    ).toBeInTheDocument();

    // Click the confirm button inside the dialog
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(api.fetchConnectionDependencies).toHaveBeenCalledWith("conn-1");
      expect(api.deleteConnection).toHaveBeenCalledWith("conn-1");
    });
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

  it("cancels delete when dialog is dismissed", async () => {
    vi.mocked(api.fetchConnections).mockResolvedValue([
      {
        id: "conn-3",
        project_id: "proj-1",
        source_type: "static_file",
        name: "Keep File",
        status: "active",
        config_json: {},
        created_at: "2026-05-18T00:00:00Z",
        updated_at: "2026-05-18T00:00:00Z",
      },
    ]);
    vi.mocked(api.fetchConnectionDependencies).mockResolvedValue({
      connection_id: "conn-3",
      active_dataset_count: 0,
      active_run_count: 0,
      can_delete: true,
    });

    render(<ConnectionsHomeContent />);

    await waitFor(() => {
      expect(screen.getByText("Keep File")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText('Delete connection "Keep File"?'),
    ).toBeInTheDocument();

    // Click cancel
    fireEvent.click(within(dialog).getByRole("button", { name: "Cancel" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(api.deleteConnection).not.toHaveBeenCalled();
  });
});
