import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { MappingReviewGrid } from "@/components/ingestion-v2/mapping-review-grid";

const mockFetchMappings = vi.fn();
const mockSaveMapping = vi.fn();

vi.mock("@/lib/api/ingestion", () => ({
  fetchMappings: (...args: unknown[]) => mockFetchMappings(...args),
  saveMapping: (...args: unknown[]) => mockSaveMapping(...args),
}));

const SAMPLE_COLUMNS = [
  {
    source_column_name: "name",
    inferred_type: "text",
    sample_values: ["Alice", "Bob"],
    null_ratio: 0,
    confidence: 0.9,
    suggested_target_field: "employee_name",
  },
  {
    source_column_name: "custom_field",
    inferred_type: "text",
    sample_values: ["foo", "bar"],
    null_ratio: 0.1,
    confidence: 0.3,
    suggested_target_field: null,
  },
];

const SAMPLE_DECISIONS = [
  {
    source_column_name: "name",
    target_field_name: "employee_name",
    confirmed: true,
    overridden_by_user: false,
  },
  {
    source_column_name: "custom_field",
    target_field_name: "",
    confirmed: false,
    overridden_by_user: false,
  },
];

beforeEach(() => {
  vi.clearAllMocks();
});

describe("MappingReviewGrid", () => {
  it("renders loading state initially", () => {
    mockFetchMappings.mockReturnValue(new Promise(() => {}));
    render(<MappingReviewGrid uploadId="test-1" />);
    expect(screen.getByText("Loading mapping suggestions...")).toBeInTheDocument();
  });

  it("renders error state on fetch failure", async () => {
    mockFetchMappings.mockRejectedValue(new Error("Network error"));
    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("renders columns from profile data", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });
    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("name")).toBeInTheDocument();
      expect(screen.getByText("custom_field")).toBeInTheDocument();
    });
  });

  it("allows manual override of target field", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });
    render(<MappingReviewGrid uploadId="test-1" />);

    await waitFor(() => {
      expect(screen.getByDisplayValue("employee_name")).toBeInTheDocument();
    });

    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "full_name" } });

    await waitFor(() => {
      expect(screen.getByDisplayValue("full_name")).toBeInTheDocument();
      expect(screen.getByText("Overridden")).toBeInTheDocument();
    });
  });

  it("flags missing required fields", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: [
        { source_column_name: "employee_id", target_field_name: "", confirmed: false, overridden_by_user: false },
        { source_column_name: "name", target_field_name: "employee_name", confirmed: true, overridden_by_user: false },
      ],
      column_profiles: [],
    });
    render(<MappingReviewGrid uploadId="test-1" />);

    await waitFor(() => {
      expect(screen.getByText("1 required field unmapped")).toBeInTheDocument();
    });
  });

  it("disables save button when required fields unmapped", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: [
        { source_column_name: "employee_id", target_field_name: "", confirmed: false, overridden_by_user: false },
      ],
      column_profiles: [],
    });
    render(<MappingReviewGrid uploadId="test-1" />);

    await waitFor(() => {
      const saveBtn = screen.getByText("Save Mappings");
      expect(saveBtn).toBeDisabled();
    });
  });

  it("recovers from error via retry", async () => {
    mockFetchMappings.mockRejectedValueOnce(new Error("First fail"));
    mockFetchMappings.mockResolvedValueOnce({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });

    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("First fail")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Try again"));
    await waitFor(() => {
      expect(screen.getByText("name")).toBeInTheDocument();
    });
  });

  it("shows saved confirmation after successful save", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });
    mockSaveMapping.mockResolvedValue(SAMPLE_DECISIONS);

    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("name")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Save Mappings"));
    await waitFor(() => {
      expect(screen.getByText("Mapping decisions saved.")).toBeInTheDocument();
    });
  });

  it("shows bulk apply button when high-confidence suggestions exist", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });

    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("Bulk Apply High-Confidence")).toBeInTheDocument();
    });
  });

  it("bulk apply fills target fields for high-confidence columns", async () => {
    mockFetchMappings.mockResolvedValue({
      upload_id: "test-1",
      decisions: SAMPLE_DECISIONS,
      column_profiles: SAMPLE_COLUMNS,
    });

    render(<MappingReviewGrid uploadId="test-1" />);
    await waitFor(() => {
      expect(screen.getByText("Bulk Apply High-Confidence")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Bulk Apply High-Confidence"));
    await waitFor(() => {
      expect(screen.getByDisplayValue("employee_name")).toBeInTheDocument();
    });
  });
});
