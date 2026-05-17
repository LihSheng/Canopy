import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mock_push = vi.fn();
const preview_grid_mock = vi.fn(({ columns, rows, totalRowCount }: { columns: string[]; rows: unknown[][]; totalRowCount: number }) => {
  return (
    <div data-testid="preview-grid">
      <div>Preview rows: {rows.length}</div>
      <div>Total rows: {totalRowCount}</div>
      <div>Columns: {columns.join(",")}</div>
    </div>
  );
});

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mock_push, replace: vi.fn() }),
  useSearchParams: () => ({
    get: (key: string) => (key === "source" ? "static_file" : null),
    toString: () => "",
  }),
}));

vi.mock("@/lib/api/data-source", () => ({
  deleteStaticFilePreview: vi.fn().mockResolvedValue({ deleted: true }),
  previewStaticFile: vi.fn(),
  fetchProjects: vi.fn().mockResolvedValue([{ id: "project-1", name: "Default Project" }]),
  createProject: vi.fn(),
  createConnection: vi.fn(),
  createDataset: vi.fn(),
}));

vi.mock("@/components/preview-grid", () => ({
  PreviewGrid: (props: { columns: string[]; rows: unknown[][]; totalRowCount: number }) =>
    preview_grid_mock(props),
}));

import SetupPage from "@/app/dashboard/connections/setup/page";
import { previewStaticFile } from "@/lib/api/data-source";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SetupPage", () => {
  it("shows a back link and renders a sheet preview after upload", async () => {
    vi.mocked(previewStaticFile).mockResolvedValue({
      source_file_path: "/tmp/sample.xlsx",
      file_name: "sample.xlsx",
      sheet_profiles: [
        {
          sheet_name: "Payroll",
          row_count: 3,
          data_row_count: 2,
          column_count: 2,
          header_row_index: 0,
          confidence: 1,
          warnings: [],
          preview_columns: ["name", "amount"],
          preview_rows: [
            ["Alice", 100],
            ["Bob", 200],
          ],
        },
      ],
    });

    render(<SetupPage />);

    expect(screen.getByRole("link", { name: "Back to sources" })).toHaveAttribute(
      "href",
      "/dashboard/connections/sources",
    );

    const input = document.querySelector("input[type='file']");
    expect(input).not.toBeNull();

    const file = new File(["name,amount\nAlice,100\nBob,200"], "sample.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    fireEvent.change(input as HTMLInputElement, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Preview: Payroll")).toBeInTheDocument();
      expect(screen.getByTestId("preview-grid")).toBeInTheDocument();
      expect(screen.getByText("Preview rows: 2")).toBeInTheDocument();
      expect(screen.getByText("Total rows: 2")).toBeInTheDocument();
      expect(screen.getByText("Columns: name,amount")).toBeInTheDocument();
    });
  });

  it("lets the user remove an uploaded file and return to the dropzone", async () => {
    vi.mocked(previewStaticFile).mockResolvedValue({
      source_file_path: "/tmp/sample.xlsx",
      file_name: "sample.xlsx",
      sheet_profiles: [
        {
          sheet_name: "Payroll",
          row_count: 3,
          data_row_count: 2,
          column_count: 2,
          header_row_index: 0,
          confidence: 1,
          warnings: [],
          preview_columns: ["name", "amount"],
          preview_rows: [["Alice", 100]],
        },
      ],
    });

    render(<SetupPage />);

    const input = document.querySelector("input[type='file']");
    const file = new File(["name,amount\nAlice,100"], "sample.xlsx", {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });

    fireEvent.change(input as HTMLInputElement, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Preview: Payroll")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Remove file" }));

    await waitFor(() => {
      expect(screen.queryByText("Preview: Payroll")).not.toBeInTheDocument();
      expect(screen.queryByRole("button", { name: "Remove file" })).not.toBeInTheDocument();
      expect(screen.getByText("browse")).toBeInTheDocument();
    });
  });

  it("shows the upload error when preview fails", async () => {
    vi.mocked(previewStaticFile).mockRejectedValue(new Error("Only .xlsx and .csv files are supported"));

    render(<SetupPage />);

    const input = document.querySelector("input[type='file']");
    const file = new File(["bad"], "sample.xls", {
      type: "application/vnd.ms-excel",
    });

    fireEvent.change(input as HTMLInputElement, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText("Only .xlsx and .csv files are supported")).toBeInTheDocument();
      expect(screen.getByText("browse")).toBeInTheDocument();
    });
  });
});
