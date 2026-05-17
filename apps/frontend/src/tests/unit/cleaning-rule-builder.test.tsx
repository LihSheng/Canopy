import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { CleaningRuleBuilder } from "@/components/ingestion-v2/cleaning-rule-builder";

const mockCreatePipeline = vi.fn();
const mockFetchPipeline = vi.fn();
const mockSaveSteps = vi.fn();
const mockReorderSteps = vi.fn();
const mockPublishPipeline = vi.fn();

vi.mock("@/lib/api/ingestion", () => ({
  createPipeline: (...args: unknown[]) => mockCreatePipeline(...args),
  fetchPipeline: (...args: unknown[]) => mockFetchPipeline(...args),
  saveSteps: (...args: unknown[]) => mockSaveSteps(...args),
  reorderSteps: (...args: unknown[]) => mockReorderSteps(...args),
  publishPipeline: (...args: unknown[]) => mockPublishPipeline(...args),
  validatePipeline: vi.fn().mockResolvedValue({ warnings: [] }),
}));

const TEST_UPLOAD_ID = "test-upload-1";
const TEST_PIPELINE_ID = "test-pipeline-1";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("CleaningRuleBuilder", () => {
  it("renders loading state initially", () => {
    mockCreatePipeline.mockReturnValue(new Promise(() => {}));
    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    expect(screen.getByText("Loading cleaning rules...")).toBeInTheDocument();
  });

  it("renders empty state when no steps exist", async () => {
    mockCreatePipeline.mockResolvedValue({
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("No cleaning rules configured yet.")).toBeInTheDocument();
    });
  });

  it("shows add step button when in draft mode", async () => {
    mockCreatePipeline.mockResolvedValue({
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("+ Add Step")).toBeInTheDocument();
    });
  });

  it("adds a step when clicking an option", async () => {
    mockCreatePipeline.mockResolvedValue({
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("+ Add Step")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Step"));
    expect(screen.getByText("Trim Whitespace")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Trim Whitespace"));
    await waitFor(() => {
      expect(screen.getByText("Trim Whitespace")).toBeInTheDocument();
    });
  });

  it("removes a step", async () => {
    mockCreatePipeline.mockResolvedValue({
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("+ Add Step")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Step"));
    fireEvent.click(screen.getByText("Trim Whitespace"));

    await waitFor(() => {
      const removeBtns = screen.getAllByText("Remove");
      expect(removeBtns.length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByText("Remove"));
    await waitFor(() => {
      expect(screen.getByText("No cleaning rules configured yet.")).toBeInTheDocument();
    });
  });

  it("shows published state when pipeline is published", async () => {
    mockCreatePipeline.mockResolvedValue({
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "published",
      steps: [
        { id: "step-1", step_type: "trim", order: 0, parameters: { columns: ["name"] }, description: null },
      ],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    });

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("Published")).toBeInTheDocument();
    });
  });

  it("calls saveSteps when save button is clicked", async () => {
    const pipeline = {
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    mockCreatePipeline.mockResolvedValue(pipeline);
    mockSaveSteps.mockResolvedValue([
      { id: "saved-1", step_type: "trim", order: 0, parameters: { columns: ["name"] }, description: null },
    ]);

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("+ Add Step")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Step"));
    fireEvent.click(screen.getByText("Trim Whitespace"));

    fireEvent.click(screen.getByText("Save Steps"));
    await waitFor(() => {
      expect(mockSaveSteps).toHaveBeenCalled();
    });
  });

  it("shows save confirmation after successful save", async () => {
    const pipeline = {
      id: TEST_PIPELINE_ID,
      upload_id: TEST_UPLOAD_ID,
      status: "draft",
      steps: [],
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-01T00:00:00Z",
    };

    mockCreatePipeline.mockResolvedValue(pipeline);
    mockSaveSteps.mockResolvedValue([
      { id: "saved-1", step_type: "trim", order: 0, parameters: { columns: ["name"] }, description: null },
    ]);

    render(<CleaningRuleBuilder uploadId={TEST_UPLOAD_ID} />);
    await waitFor(() => {
      expect(screen.getByText("+ Add Step")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("+ Add Step"));
    fireEvent.click(screen.getByText("Trim Whitespace"));

    fireEvent.click(screen.getByText("Save Steps"));
    await waitFor(() => {
      expect(screen.getByText("Steps saved.")).toBeInTheDocument();
    });
  });
});
