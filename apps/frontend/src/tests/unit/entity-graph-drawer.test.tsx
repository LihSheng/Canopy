import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { NodeEditDrawer } from "@/components/entity-graph/node-edit-drawer";

// ─── Fixtures ───

const entityNode = {
  id: "entity",
  type: "default",
  data: {
    label: "employee",
    nodeType: "entity" as const,
    properties: [
      {
        source_column: "id",
        property_name: "ID",
        semantic_type: "integer",
        included: true,
        is_primary_key: true,
      },
      {
        source_column: "name",
        property_name: "Name",
        semantic_type: "string",
        included: true,
        is_primary_key: false,
      },
    ],
  },
};

const sourceNode = {
  id: "source-node-src-1",
  type: "default",
  data: {
    label: "employees_raw",
    nodeType: "source" as const,
    sourceType: "dataset_table",
    fields: ["id", "name", "email", "dept_id"],
  },
};

const datasetNode = {
  id: "dataset",
  type: "default",
  data: {
    label: "HR Dataset",
    nodeType: "dataset" as const,
  },
};

const targetNode = {
  id: "target-ot-dept",
  type: "default",
  data: {
    label: "Department",
    nodeType: "target" as const,
    linkInfo: {
      link_id: "dept_link",
      source_property_key: "dept_id",
      target_property_key: "id",
      cardinality: "many_to_one",
    },
  },
};

const mockSourceNodes = [
  {
    source_id: "src-1",
    name: "employees_raw",
    source_type: "dataset_table",
    fields: ["id", "name", "email", "dept_id"],
  },
];

// ─── Tests ───

describe("NodeEditDrawer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ─── Entity Node Editing ───

  it("renders entity properties when entity node is selected", () => {
    render(
      <NodeEditDrawer
        node={entityNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("Entity: employee")).toBeInTheDocument();
    expect(screen.getByText("ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
  });

  it("shows property details including type and PK status", () => {
    render(
      <NodeEditDrawer
        node={entityNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("integer")).toBeInTheDocument();
    expect(screen.getByText("string")).toBeInTheDocument();
    expect(screen.getByText("PK")).toBeInTheDocument();
  });

  it("shows '+ Map field' button for entity nodes with source nodes", () => {
    render(
      <NodeEditDrawer
        node={entityNode}
        sourceNodes={mockSourceNodes}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("+ Map field")).toBeInTheDocument();
  });

  it("opens field mapper when '+ Map field' is clicked", () => {
    render(
      <NodeEditDrawer
        node={entityNode}
        sourceNodes={mockSourceNodes}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("+ Map field"));

    expect(screen.getByText("Map source field to property")).toBeInTheDocument();
    expect(screen.getByText("Create Property")).toBeInTheDocument();
  });

  it("calls onUpdateProperties when a new property is created", () => {
    const onUpdate = vi.fn();
    render(
      <NodeEditDrawer
        node={entityNode}
        sourceNodes={mockSourceNodes}
        onClose={vi.fn()}
        onUpdateProperties={onUpdate}
      />
    );

    fireEvent.click(screen.getByText("+ Map field"));

    // Select a source field (first select in the mapper)
    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[0], { target: { value: "email" } });

    // Set property name
    const nameInput = screen.getByPlaceholderText("e.g. employee_id");
    fireEvent.change(nameInput, { target: { value: "Email" } });

    // Click create
    fireEvent.click(screen.getByText("Create Property"));

    expect(onUpdate).toHaveBeenCalled();
    const newProps = onUpdate.mock.calls[0][0];
    expect(newProps).toHaveLength(3); // original 2 + new 1
    expect(newProps[2]).toMatchObject({
      source_column: "email",
      property_name: "Email",
      semantic_type: "string",
      included: true,
    });
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <NodeEditDrawer
        node={entityNode}
        onClose={onClose}
        onUpdateProperties={vi.fn()}
      />
    );

    const buttons = screen.getAllByRole("button");
    const closeBtn = buttons.find((btn) =>
      btn.innerHTML.includes("M6 18L18 6")
    );
    if (closeBtn) fireEvent.click(closeBtn);

    expect(onClose).toHaveBeenCalled();
  });

  // ─── Source Node (Read-only) ───

  it("shows source fields when source node is selected", () => {
    render(
      <NodeEditDrawer
        node={sourceNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("Source: employees_raw")).toBeInTheDocument();
    expect(screen.getByText("dataset_table")).toBeInTheDocument();
    expect(screen.getByText("id")).toBeInTheDocument();
    expect(screen.getByText("email")).toBeInTheDocument();
    expect(screen.getByText("dept_id")).toBeInTheDocument();
  });

  it("shows read-only badge on source node drawer", () => {
    render(
      <NodeEditDrawer
        node={sourceNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("Read only")).toBeInTheDocument();
  });

  // ─── Dataset Node (Read-only) ───

  it("shows read-only info for dataset node", () => {
    render(
      <NodeEditDrawer
        node={datasetNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("Dataset: HR Dataset")).toBeInTheDocument();
    expect(screen.getByText("Read only")).toBeInTheDocument();
    expect(
      screen.getByText(/system facts and cannot be edited/i)
    ).toBeInTheDocument();
  });

  // ─── Target Node ───

  it("shows link info for target reference node", () => {
    render(
      <NodeEditDrawer
        node={targetNode}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(screen.getByText("Target: Department")).toBeInTheDocument();
    expect(screen.getByText("Entity Link Reference")).toBeInTheDocument();
    expect(screen.getByText("dept_link")).toBeInTheDocument();
    expect(screen.getByText("many_to_one")).toBeInTheDocument();
  });

  // ─── Empty state ───

  it("shows empty state when node has no properties or fields", () => {
    render(
      <NodeEditDrawer
        node={{ id: "empty", type: "default", data: { label: "Empty", nodeType: "entity", properties: [] } }}
        sourceNodes={[]}
        onClose={vi.fn()}
        onUpdateProperties={vi.fn()}
      />
    );

    expect(
      screen.getByText(/No properties defined yet/i)
    ).toBeInTheDocument();
    expect(screen.getByText("+ Map field")).toBeInTheDocument();
  });
});
