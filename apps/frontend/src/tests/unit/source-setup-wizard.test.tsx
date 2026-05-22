import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

const mockPush = vi.fn();
const mockSearchParamsGet = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => ({ get: mockSearchParamsGet }),
}));

vi.mock("@/components/data-studio/sync-policy-editor", () => ({
  SyncPolicyEditor: ({ tableName, value: _value }: { tableName: string; value: unknown }) => (
    <div data-testid="sync-policy-editor">{tableName}</div>
  ),
}));

import { SourceSetupWizard } from "@/components/data-studio/source-setup-wizard";

const mockCreateConnection = vi.fn();
const mockFetchConnectionTest = vi.fn();
const mockFetchTableDiscovery = vi.fn();
const mockCreateDataset = vi.fn();
const mockPreviewStaticFile = vi.fn();
const mockDeleteStaticFilePreview = vi.fn();
const mockCreateProject = vi.fn();

vi.mock("@/lib/api/data-source", () => ({
  createConnection: (...args: unknown[]) => mockCreateConnection(...args),
  fetchConnectionTest: (...args: unknown[]) => mockFetchConnectionTest(...args),
  fetchTableDiscovery: (...args: unknown[]) => mockFetchTableDiscovery(...args),
  createDataset: (...args: unknown[]) => mockCreateDataset(...args),
  previewStaticFile: (...args: unknown[]) => mockPreviewStaticFile(...args),
  deleteStaticFilePreview: (...args: unknown[]) => mockDeleteStaticFilePreview(...args),
  createProject: (...args: unknown[]) => mockCreateProject(...args),
}));

describe("SourceSetupWizard — DB source (postgresql)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParamsGet.mockReturnValue("postgresql");
    mockCreateConnection.mockResolvedValue({ id: "conn-1", project_id: "proj-1" });
    mockFetchConnectionTest.mockResolvedValue({ success: true, supports_cdc: true });
    mockFetchTableDiscovery.mockResolvedValue([
      {
        table_name: "users",
        row_count_estimate: 1000,
        columns: [{ name: "id", data_type: "bigint" }],
        detected_cursor_column: "updated_at",
      },
    ]);
    mockCreateDataset.mockResolvedValue({ id: "ds-1" });
  });

  it("shows DB connection form with PostgreSQL as source type", () => {
    render(<SourceSetupWizard />);
    expect(screen.getByText("Connect Database")).toBeInTheDocument();
    expect(screen.getByDisplayValue("PostgreSQL")).toBeInTheDocument();
  });

  it("shows correct default port for PostgreSQL", () => {
    render(<SourceSetupWizard />);
    expect(screen.getByDisplayValue("5432")).toBeInTheDocument();
  });

  it("disables Test Connection when host or database is empty", () => {
    render(<SourceSetupWizard />);
    const testButton = screen.getByText("Test Connection");
    expect(testButton).toBeDisabled();
  });

  it("enables Test Connection after filling host and database", () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "db.example.com" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "production" } });
    expect(screen.getByText("Test Connection")).not.toBeDisabled();
  });

  it("shows success badge after test passes", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(screen.getByText("Connection successful")).toBeInTheDocument();
    });
  });

  it("shows error when fetchConnectionTest returns success=false", async () => {
    mockFetchConnectionTest.mockResolvedValue({ success: false, message: "Access denied" });
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(screen.getByText("Access denied")).toBeInTheDocument();
    });
  });

  it("shows error when createConnection throws", async () => {
    mockCreateConnection.mockRejectedValue(new Error("Network failure"));
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(screen.getByText("Network failure")).toBeInTheDocument();
    });
  });

  it("disables Next button until test succeeds", () => {
    render(<SourceSetupWizard />);
    const nextButton = screen.getByText("Next");
    expect(nextButton).toBeDisabled();
  });

  it("enables Next after successful test", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(screen.getByText("Next")).not.toBeDisabled();
    });
  });

  it("advances to step 2 and shows discovered tables", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => {
      expect(screen.getByText("Select Tables")).toBeInTheDocument();
      expect(screen.getByText("users")).toBeInTheDocument();
    });
  });

  it("toggles table selection in step 2", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => expect(screen.getByText("users")).toBeInTheDocument());

    const checkbox = screen.getByRole("checkbox", { name: /users/i });
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    expect(checkbox).toBeChecked();
  });

  it("shows error when fetchTableDiscovery throws", async () => {
    mockFetchTableDiscovery.mockRejectedValue(new Error("timeout"));
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => {
      expect(screen.getByText("Failed to discover tables")).toBeInTheDocument();
    });
  });

  it("advances to step 3 and shows sync policy editors", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => expect(screen.getByText("users")).toBeInTheDocument());

    // Select table and proceed
    fireEvent.click(screen.getByRole("checkbox", { name: /users/i }));
    fireEvent.click(screen.getByText(/Next.*1/));
    await waitFor(() => {
      expect(screen.getByText("Configure Sync Policy")).toBeInTheDocument();
    });
    expect(screen.getByTestId("sync-policy-editor")).toHaveTextContent("users");
  });

  it("creates datasets and redirects on finish", async () => {
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => expect(screen.getByText("users")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("checkbox", { name: /users/i }));
    fireEvent.click(screen.getByText(/Next.*1/));
    await waitFor(() => expect(screen.getByText("Configure Sync Policy")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Finish & Deploy"));
    await waitFor(() => {
      expect(mockCreateDataset).toHaveBeenCalledWith(
        expect.objectContaining({ name: "users", connection_id: "conn-1" }),
      );
      expect(mockPush).toHaveBeenCalledWith("/dashboard/connections/datasets");
    });
  });

  it("shows error when createDataset throws on finish", async () => {
    mockCreateDataset.mockRejectedValue(new Error("DB error"));
    render(<SourceSetupWizard />);
    fireEvent.change(screen.getByPlaceholderText("localhost"), { target: { value: "host" } });
    fireEvent.change(screen.getByPlaceholderText("mydb"), { target: { value: "db" } });
    fireEvent.click(screen.getByText("Test Connection"));
    await waitFor(() => expect(screen.getByText("Connection successful")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Next"));
    await waitFor(() => expect(screen.getByText("users")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("checkbox", { name: /users/i }));
    fireEvent.click(screen.getByText(/Next.*1/));
    await waitFor(() => expect(screen.getByText("Configure Sync Policy")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Finish & Deploy"));
    await waitFor(() => {
      // Component catches the error and displays its message via err.message
      expect(screen.getByText("DB error")).toBeInTheDocument();
    });
  });

  it("shows Back to Sources button on step 1", () => {
    render(<SourceSetupWizard />);
    expect(screen.getByText("Back to Sources")).toBeInTheDocument();
  });
});

describe("SourceSetupWizard — Static file source", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParamsGet.mockReturnValue(null); // no source = static_file
    mockPreviewStaticFile.mockResolvedValue({
      source_file_path: "/tmp/test.xlsx",
      file_name: "test.xlsx",
      sheet_profiles: [
        {
          sheet_name: "Sheet1",
          row_count: 100,
          data_row_count: 95,
          column_count: 5,
          header_row_index: 0,
          confidence: 0.95,
          warnings: [],
          preview_columns: ["A", "B", "C"],
          preview_rows: [["1", "2", "3"]],
        },
      ],
    });
    mockCreateProject.mockResolvedValue({ id: "proj-1" });
    mockCreateConnection.mockResolvedValue({ id: "conn-1" });
    mockCreateDataset.mockResolvedValue({ id: "ds-1" });
  });

  it("shows upload UI by default", () => {
    render(<SourceSetupWizard />);
    expect(screen.getByText("Upload File")).toBeInTheDocument();
    expect(screen.getByText(/Drop your file here/)).toBeInTheDocument();
  });

  it("shows step indicator without Sync Policy step", () => {
    render(<SourceSetupWizard />);
    expect(screen.getByText("Upload")).toBeInTheDocument();
    expect(screen.getByText("Select Objects")).toBeInTheDocument();
    expect(screen.queryByText("Sync Policy")).not.toBeInTheDocument();
  });

  it("processes file upload via file input", async () => {
    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");

    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockPreviewStaticFile).toHaveBeenCalledWith(file, "static_file");
    });
  });

  it("advances to step 2 after file upload with sheet names", async () => {
    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Select Sheets")).toBeInTheDocument();
      expect(screen.getByText("Sheet1")).toBeInTheDocument();
    });
  });

  it("advances to step 2 after file upload", async () => {
    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Select Sheets")).toBeInTheDocument();
    });
  });

  it("shows select-all checkbox in step 2 for static files", async () => {
    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Select Sheets")).toBeInTheDocument();
    });

    expect(screen.getByText("Select All")).toBeInTheDocument();
    expect(screen.getByText("1 of 1 selected")).toBeInTheDocument();
  });

  it("creates project + connection + dataset and redirects on finish", async () => {
    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Select Sheets")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Finish & Deploy"));

    await waitFor(() => {
      expect(mockCreateProject).toHaveBeenCalledWith({ name: "Default Project" });
      expect(mockCreateConnection).toHaveBeenCalledWith(
        expect.objectContaining({ source_type: "static_file" }),
      );
      expect(mockCreateDataset).toHaveBeenCalledWith(
        expect.objectContaining({ name: "Sheet1" }),
      );
      expect(mockPush).toHaveBeenCalledWith("/dashboard/connections/datasets");
    });
  });

  it("stays on step 1 with error when previewStaticFile throws", async () => {
    mockPreviewStaticFile.mockRejectedValue(new Error("Invalid file"));

    render(<SourceSetupWizard />);

    const file = new File(["bad"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    // Error is shown on Step 1 (Upload step), not Step 2
    await waitFor(() => {
      expect(screen.getByText("Invalid file")).toBeInTheDocument();
    });
    expect(screen.getByText("Upload File")).toBeInTheDocument();
  });

  it("shows error when finish fails for static file", async () => {
    mockCreateDataset.mockRejectedValue(new Error("Upload error"));

    render(<SourceSetupWizard />);

    const file = new File(["a,b\n1,2"], "test.xlsx", { type: "application/vnd.ms-excel" });
    const input = screen.getByTestId("file-input");
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Select Sheets")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Finish & Deploy"));
    await waitFor(() => {
      // Component catches the error and displays its message via err.message
      expect(screen.getByText("Upload error")).toBeInTheDocument();
    });
  });
});
