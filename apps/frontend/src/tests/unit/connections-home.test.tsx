import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import ConnectionsHomeContent from "@/app/dashboard/connections/connections-home-content";

// Mock API calls
vi.mock("@/lib/api/data-source", () => ({
  fetchConnections: vi.fn().mockResolvedValue([]),
  fetchDatasets: vi.fn().mockResolvedValue([]),
  fetchRuns: vi.fn().mockResolvedValue([]),
  fetchConnectionDependencies: vi.fn(),
  deleteConnection: vi.fn(),
}));

describe("ConnectionsHomeContent", () => {
  it("shows only 'Add New Connection' button and no Source Catalog button", async () => {
    render(<ConnectionsHomeContent />);
    
    // Wait for loading to finish
    await waitFor(() => {
      expect(screen.queryByText("Loading...")).not.toBeInTheDocument();
    });

    // Check for "New Connection"
    expect(screen.getByText("+ New Connection")).toBeInTheDocument();
    
    // Verify "Source Catalog" button is NOT there (neither as button nor link)
    expect(screen.queryByText("Source Catalog")).not.toBeInTheDocument();
  });
});
