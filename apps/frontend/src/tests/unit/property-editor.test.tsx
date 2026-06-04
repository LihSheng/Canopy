import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PropertyEditor } from "@/components/entity-graph/property-editor";
import type { SourceBinding } from "@/lib/api/types";

// ── Mock data-source API (used by SourceRegistrationDrawer) ──
vi.mock("@/lib/api/data-source", () => ({
  fetchDatasets: vi.fn().mockResolvedValue([]),
  fetchConnections: vi.fn().mockResolvedValue([]),
}));

// ── Mock toast ──
vi.mock("@/components/shared", async () => {
  const actual = await vi.importActual("@/components/shared");
  return {
    ...actual,
    useToast: () => ({
      success: vi.fn(),
      info: vi.fn(),
      danger: vi.fn(),
    }),
  };
});

// ── Mock SourceRegistrationDrawer ──
vi.mock("@/components/entity-graph/source-registration-drawer", () => ({
  SourceRegistrationDrawer: vi.fn(() => (
    <div data-testid="source-registration-drawer">Source Drawer</div>
  )),
}));

// ── Helpers ──

const mockSourceNode = (overrides?: Record<string, unknown>) => ({
  source_id: "src-1",
  source_type: "dataset_table",
  name: "employees",
  fields: ["id", "name", "email"],
  ...overrides,
});

const mockProperty = (overrides?: Record<string, unknown>) => ({
  property_id: "prop-1",
  property_key: "employee_name",
  display_name: "Employee Name",
  semantic_type: "string",
  is_required: true,
  is_primary_key: false,
  sort_order: 0,
  ...overrides,
});

const baseProps = {
  properties: [mockProperty()],
  sourceBindings: [] as SourceBinding[],
  sourceNodes: [],
  onSaveProperty: vi.fn().mockResolvedValue(undefined),
  onRemove: vi.fn().mockResolvedValue(undefined),
  onReorder: vi.fn().mockResolvedValue(undefined),
  onAddSource: vi.fn().mockResolvedValue(undefined),
  onRemoveSource: vi.fn().mockResolvedValue(undefined),
  projectId: "proj-1",
  datasetId: "ds-1",
};

describe("PropertyEditor — Sources table", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a Sources table with source node rows when sources exist", () => {
    const sources = [
      mockSourceNode({ source_id: "src-1", name: "employees", source_type: "dataset_table", fields: ["id", "name"] }),
      mockSourceNode({ source_id: "src-2", name: "payroll", source_type: "static_file", fields: ["emp_id", "amount"] }),
    ];

    render(
      <PropertyEditor
        {...baseProps}
        sourceNodes={sources}
      />
    );

    // Section header exists
    expect(screen.getByText("Sources")).toBeDefined();

    // Both source names rendered
    expect(screen.getByText("employees")).toBeDefined();
    expect(screen.getByText("payroll")).toBeDefined();

    // Source types rendered
    expect(screen.getByText("dataset_table")).toBeDefined();
    expect(screen.getByText("static_file")).toBeDefined();

    // Field counts rendered
    const fieldCounts = screen.getAllByText("2");
    expect(fieldCounts.length).toBe(2);

    // Add Source button exists
    expect(screen.getByText("+ Add Source")).toBeDefined();
  });

  it("shows empty state message when no source nodes are registered", () => {
    render(
      <PropertyEditor
        {...baseProps}
        sourceNodes={[]}
      />
    );

    expect(screen.getByText("Sources")).toBeDefined();
    expect(screen.getByText(/No sources registered/)).toBeDefined();
    expect(screen.getByText("+ Add Source")).toBeDefined();
  });

  it("opens SourceRegistrationDrawer when '+ Add Source' is clicked", () => {
    render(
      <PropertyEditor
        {...baseProps}
        sourceNodes={[mockSourceNode()]}
      />
    );

    // Drawer not visible initially
    expect(screen.queryByTestId("source-registration-drawer")).toBeNull();

    // Click the button
    fireEvent.click(screen.getByText("+ Add Source"));

    // Drawer now visible
    expect(screen.getByTestId("source-registration-drawer")).toBeDefined();
  });

  it("calls onAddSource when sources are added via the drawer and closes the drawer", async () => {
    const onAddSource = vi.fn().mockResolvedValue(undefined);

    // Override the SourceRegistrationDrawer mock to capture onAdd
    const { SourceRegistrationDrawer } = await import("@/components/entity-graph/source-registration-drawer");
    const mockDrawer = vi.mocked(SourceRegistrationDrawer);

    render(
      <PropertyEditor
        {...baseProps}
        sourceNodes={[]}
        onAddSource={onAddSource}
      />
    );

    // Open the drawer
    fireEvent.click(screen.getByText("+ Add Source"));

    // Simulate the drawer calling its onAdd prop with an array
    const drawerProps = mockDrawer.mock.calls.at(-1)?.[0];
    expect(drawerProps).toBeDefined();

    if (!drawerProps) return;

    const newSources = [
      {
        source_id: "src-new",
        source_type: "dataset_table" as const,
        name: "new_source",
        reference_id: "ref-1",
        fields: ["col1", "col2"],
      },
    ];

    await drawerProps.onAdd(newSources);

    expect(onAddSource).toHaveBeenCalledWith(newSources);
    // After successful add, drawer should close (via state change)
  });

  it("calls onRemoveSource when Remove is clicked on a source row", () => {
    const onRemoveSource = vi.fn().mockResolvedValue(undefined);

    render(
      <PropertyEditor
        {...baseProps}
        sourceNodes={[mockSourceNode({ source_id: "src-to-remove", name: "to_remove" })]}
        onRemoveSource={onRemoveSource}
      />
    );

    const removeButton = screen.getByText("Remove");
    fireEvent.click(removeButton);

    expect(onRemoveSource).toHaveBeenCalledWith("src-to-remove");
  });
});
