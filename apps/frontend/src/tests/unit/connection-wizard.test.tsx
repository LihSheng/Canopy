import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ConnectionWizard } from "@/components/data-studio/connection-wizard";

const mockPush = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/lib/api/data-source", () => ({
  createConnection: vi.fn().mockResolvedValue({
    id: "conn-1",
    project_id: "proj-1",
    source_type: "postgresql",
    name: "test",
    status: "active",
  }),
  fetchConnectionTest: vi.fn().mockResolvedValue({ success: true }),
  fetchTableDiscovery: vi.fn().mockResolvedValue([
    {
      table_name: "users",
      row_count_estimate: 1000,
      columns: [
        { name: "id", data_type: "bigint" },
        { name: "updated_at", data_type: "timestamp" },
      ],
      detected_cursor_column: "updated_at",
    },
    {
      table_name: "orders",
      row_count_estimate: 50000,
      columns: [
        { name: "id", data_type: "bigint" },
        { name: "created_at", data_type: "timestamp" },
      ],
      detected_cursor_column: null,
    },
  ]),
  createDataset: vi.fn().mockResolvedValue({ id: "ds-1" }),
}));

describe("ConnectionWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows step 1 (Authenticate) by default", () => {
    render(<ConnectionWizard />);
    expect(screen.getByText("Connect Database")).toBeInTheDocument();
    expect(screen.getByText("Test Connection")).toBeInTheDocument();
  });

  it("shows step indicator with Authenticate as active", () => {
    render(<ConnectionWizard />);
    const steps = screen.getAllByText(/Authenticate|Select Objects|Sync Policy/);
    expect(steps[0]).toHaveTextContent("Authenticate");
    expect(steps[1]).toHaveTextContent("Select Objects");
    expect(steps[2]).toHaveTextContent("Sync Policy");
  });

  it("has source type dropdown with PostgreSQL and MySQL", () => {
    render(<ConnectionWizard />);
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    expect(screen.getByText("MySQL")).toBeInTheDocument();
  });

  it("disables Next button when connection not tested", () => {
    render(<ConnectionWizard />);
    const nextButton = screen.getByText("Next");
    expect(nextButton).toBeDisabled();
  });

  it("enables Next after successful test", async () => {
    render(<ConnectionWizard />);

    // Fill in required fields
    fireEvent.change(screen.getByPlaceholderText("localhost"), {
      target: { value: "db.example.com" },
    });
    fireEvent.change(screen.getByPlaceholderText("mydb"), {
      target: { value: "production" },
    });

    // Click Test Connection
    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(screen.getByText("Connection successful")).toBeInTheDocument();
    });

    // Next should now be enabled
    const nextButton = screen.getByText("Next");
    expect(nextButton).not.toBeDisabled();
  });

  it("shows table list in step 2 after clicking Next", async () => {
    render(<ConnectionWizard />);

    fireEvent.change(screen.getByPlaceholderText("localhost"), {
      target: { value: "host" },
    });
    fireEvent.change(screen.getByPlaceholderText("mydb"), {
      target: { value: "db" },
    });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => {
      expect(screen.getByText("users")).toBeInTheDocument();
      expect(screen.getByText("orders")).toBeInTheDocument();
    });
  });
});
