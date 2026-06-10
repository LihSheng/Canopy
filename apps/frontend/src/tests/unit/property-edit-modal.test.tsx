import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PropertyEditModal } from "@/components/entity-graph/property-edit-modal";
import type { EntityRevisionProperty } from "@/lib/api/types";

// ── Mock data-source API ──
vi.mock("@/lib/api/data-source", () => ({
  fetchDatasets: vi.fn().mockResolvedValue([]),
  fetchConnections: vi.fn().mockResolvedValue([]),
}));

// ── Mock SourceRegistrationDrawer ──
vi.mock("@/components/entity-graph/source-registration-drawer", () => ({
  SourceRegistrationDrawer: vi.fn(() => (
    <div data-testid="source-registration-drawer">Source Drawer</div>
  )),
}));

// ── Helpers ──

const mockSourceNode = (overrides?: Record<string, unknown>) => ({
  source_id: "src-1",
  name: "employees",
  source_type: "dataset_table",
  fields: ["id", "name", "email"],
  ...overrides,
});

const mockProperty = (overrides?: Record<string, unknown>): EntityRevisionProperty => ({
  property_id: "prop-1",
  property_key: "employee_name",
  display_name: "Employee Name",
  semantic_type: "string",
  is_required: true,
  is_primary_key: false,
  sort_order: 0,
  format_hint: "",
  ...overrides,
});

const baseProps = {
  open: true,
  property: null, // create mode
  existingBinding: null,
  sourceNodes: [],
  onSave: vi.fn().mockResolvedValue(undefined),
  onClose: vi.fn(),
  onAddSource: vi.fn().mockResolvedValue(undefined),
  projectId: "proj-1",
  datasetId: "ds-1",
};

describe("PropertyEditModal — Source binding table", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders source binding as a table with one row per source node", () => {
    const sources = [
      mockSourceNode({ source_id: "src-1", name: "employees", fields: ["id", "name"] }),
      mockSourceNode({ source_id: "src-2", name: "payroll", fields: ["emp_id"] }),
    ];

    render(
      <PropertyEditModal
        {...baseProps}
        sourceNodes={sources}
      />
    );

    // Table headers
    expect(screen.getByText("Source")).toBeDefined();
    expect(screen.getByText("Field")).toBeDefined();

    // Source names visible
    expect(screen.getByText("employees")).toBeDefined();
    expect(screen.getByText("payroll")).toBeDefined();

    // Field count labels
    expect(screen.getByText("2 fields")).toBeDefined(); // employees
    expect(screen.getByText("1 field")).toBeDefined(); // payroll

    // Add Source button in modal
    expect(screen.getByText("+ Add Source")).toBeDefined();
  });

  it("binds property to source field when a field is selected from dropdown", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    const sources = [
      mockSourceNode({ source_id: "src-1", name: "employees", fields: ["id", "name"] }),
    ];

    render(
      <PropertyEditModal
        {...baseProps}
        sourceNodes={sources}
        onSave={onSave}
      />
    );

    // Fill required fields
    const displayNameInput = screen.getByLabelText("Display Name");
    fireEvent.change(displayNameInput, { target: { value: "Employee Name" } });

    const keyInput = screen.getByLabelText("Key");
    fireEvent.change(keyInput, { target: { value: "employee_name" } });

    // Select a field from the source dropdown (the second combobox on the page)
    const selects = screen.getAllByRole("combobox");
    const fieldSelect = selects[1]; // first is Type, second is source field
    fireEvent.change(fieldSelect, { target: { value: "name" } });

    // Click Save
    fireEvent.click(screen.getByText("Save"));

    await vi.waitFor(() => {
      expect(onSave).toHaveBeenCalledTimes(1);
    });

    const saveCall = onSave.mock.calls[0][0];
    expect(saveCall.propertyFields.display_name).toBe("Employee Name");
    expect(saveCall.propertyFields.property_key).toBe("employee_name");
    expect(saveCall.binding).toEqual({
      property_key: "employee_name",
      source_node_id: "src-1",
      source_field_name: "name",
    });
  });

  it("opens SourceRegistrationDrawer when '+ Add Source' is clicked in modal", () => {
    render(
      <PropertyEditModal
        {...baseProps}
        sourceNodes={[]}
      />
    );

    // Drawer not visible initially
    expect(screen.queryByTestId("source-registration-drawer")).toBeNull();

    // Click Add Source
    fireEvent.click(screen.getByText("+ Add Source"));

    // Drawer visible
    expect(screen.getByTestId("source-registration-drawer")).toBeDefined();
  });
});
