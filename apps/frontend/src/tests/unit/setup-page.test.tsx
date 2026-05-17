import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mock_push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mock_push, replace: vi.fn() }),
  useSearchParams: () => ({
    get: (key: string) => (key === "source" ? "static_file" : null),
    toString: () => "",
  }),
}));

vi.mock("@/lib/api/data-source", () => ({
  previewStaticFile: vi.fn(),
  fetchProjects: vi.fn().mockResolvedValue([{ id: "project-1", name: "Default Project" }]),
  createProject: vi.fn(),
  createConnection: vi.fn(),
  createDataset: vi.fn(),
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
      expect(screen.getByText("Alice")).toBeInTheDocument();
      expect(screen.getByText("Bob")).toBeInTheDocument();
    });
  });
});
