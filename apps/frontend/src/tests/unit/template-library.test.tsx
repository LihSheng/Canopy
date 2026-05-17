import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { TemplateLibrary } from "@/components/ingestion-v2/template-library";

const mockFetchTemplateFamilies = vi.fn();
const mockFetchTemplateFamily = vi.fn();
const mockCreateTemplateFamily = vi.fn();
const mockCreateTemplateVersion = vi.fn();
const mockPublishTemplateVersion = vi.fn();
const mockBindPipelineToTemplate = vi.fn();

vi.mock("@/lib/api/ingestion", () => ({
  fetchTemplateFamilies: (...args: unknown[]) => mockFetchTemplateFamilies(...args),
  fetchTemplateFamily: (...args: unknown[]) => mockFetchTemplateFamily(...args),
  createTemplateFamily: (...args: unknown[]) => mockCreateTemplateFamily(...args),
  createTemplateVersion: (...args: unknown[]) => mockCreateTemplateVersion(...args),
  publishTemplateVersion: (...args: unknown[]) => mockPublishTemplateVersion(...args),
  bindPipelineToTemplate: (...args: unknown[]) => mockBindPipelineToTemplate(...args),
}));

const TEST_FAMILIES = [
  {
    id: "fam-1",
    dataset_type: "payroll",
    source_profile: "herdhr",
    name: "Payroll Standard",
    description: "Standard payroll template",
    status: "active",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "fam-2",
    dataset_type: "expenses",
    source_profile: "herdhr",
    name: "Expense Cleanup",
    description: "",
    status: "active",
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  },
];

const TEST_FAMILY_DETAIL = {
  ...TEST_FAMILIES[0],
  versions: [
    {
      id: "ver-1",
      template_id: "fam-1",
      version_number: 1,
      state: "published",
      spec_json: { steps: [{ type: "trim" }] },
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
      published_at: "2026-01-01T12:00:00Z",
    },
    {
      id: "ver-2",
      template_id: "fam-1",
      version_number: 2,
      state: "draft",
      spec_json: { steps: [] },
      created_at: "2026-01-02T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
      published_at: null,
    },
  ],
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("TemplateLibrary", () => {
  it("renders loading state initially", () => {
    mockFetchTemplateFamilies.mockReturnValue(new Promise(() => {}));
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    expect(screen.getByText("Loading template library...")).toBeInTheDocument();
  });

  it("renders empty state when no families exist", async () => {
    mockFetchTemplateFamilies.mockResolvedValue([]);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("No template families found.")).toBeInTheDocument();
    });
  });

  it("renders list of template families", async () => {
    mockFetchTemplateFamilies.mockResolvedValue(TEST_FAMILIES);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("Payroll Standard")).toBeInTheDocument();
      expect(screen.getByText("Expense Cleanup")).toBeInTheDocument();
    });
  });

  it("shows create form when clicking new template button", async () => {
    mockFetchTemplateFamilies.mockResolvedValue([]);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("+ New Template")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("+ New Template"));
    expect(screen.getByText("New Template Family")).toBeInTheDocument();
  });

  it("views template family detail", async () => {
    mockFetchTemplateFamilies.mockResolvedValue(TEST_FAMILIES);
    mockFetchTemplateFamily.mockResolvedValue(TEST_FAMILY_DETAIL);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("Payroll Standard")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Payroll Standard"));
    await waitFor(() => {
      expect(screen.getByText("v1")).toBeInTheDocument();
      expect(screen.getByText("v2")).toBeInTheDocument();
    });
  });

  it("shows publish button for draft versions", async () => {
    mockFetchTemplateFamilies.mockResolvedValue(TEST_FAMILIES);
    mockFetchTemplateFamily.mockResolvedValue(TEST_FAMILY_DETAIL);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("Payroll Standard")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Payroll Standard"));
    await waitFor(() => {
      const publishButtons = screen.getAllByText("Publish");
      expect(publishButtons.length).toBeGreaterThan(0);
    });
  });

  it("shows bind button for published versions", async () => {
    mockFetchTemplateFamilies.mockResolvedValue(TEST_FAMILIES);
    mockFetchTemplateFamily.mockResolvedValue(TEST_FAMILY_DETAIL);
    render(
      <TemplateLibrary uploadId="up-1" pipelineId="pl-1" onBound={vi.fn()} />,
    );
    await waitFor(() => {
      expect(screen.getByText("Payroll Standard")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Payroll Standard"));
    await waitFor(() => {
      expect(screen.getByText("Bind to Upload")).toBeInTheDocument();
    });
  });
});
