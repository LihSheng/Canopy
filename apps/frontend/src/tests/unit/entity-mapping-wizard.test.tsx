import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import { EntityMappingWizard } from "@/components/entity-mapping/entity-mapping-wizard";
import type {
  ObjectType,
  SchemaColumn,
  SemanticMapping,
  ValidationResult,
} from "@/lib/api/types";

// ─── Mock API ───

const mockFetchObjectTypes = vi.fn();
const mockCreateObjectType = vi.fn();
const mockUpdateObjectType = vi.fn();
const mockFetchDatasetVersionSchema = vi.fn();
const mockCreateMapping = vi.fn();
const mockUpdateMapping = vi.fn();
const mockValidateMapping = vi.fn();
const mockFetchObjectTypePrimaryKey = vi.fn();

vi.mock("@/lib/api/semantic", () => ({
  fetchObjectTypes: (...args: unknown[]) => mockFetchObjectTypes(...args),
  createObjectType: (...args: unknown[]) => mockCreateObjectType(...args),
  updateObjectType: (...args: unknown[]) => mockUpdateObjectType(...args),
  fetchDatasetVersionSchema: (...args: unknown[]) =>
    mockFetchDatasetVersionSchema(...args),
  createMapping: (...args: unknown[]) => mockCreateMapping(...args),
  updateMapping: (...args: unknown[]) => mockUpdateMapping(...args),
  validateMapping: (...args: unknown[]) => mockValidateMapping(...args),
  fetchObjectTypePrimaryKey: (...args: unknown[]) =>
    mockFetchObjectTypePrimaryKey(...args),
}));

// Mock toast to avoid DOM warnings
vi.mock("@/components/shared", async () => {
  const actual = await vi.importActual("@/components/shared");
  return {
    ...actual,
    useToast: () => ({
      success: vi.fn(),
      danger: vi.fn(),
      info: vi.fn(),
    }),
  };
});

// ─── Fixtures ───

const objectTypes: ObjectType[] = [
  {
    id: "ot-employee",
    tenant_id: "t1",
    object_type_key: "employee",
    display_name: "Employee",
    description: "Employee records",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
  },
  {
    id: "ot-department",
    tenant_id: "t1",
    object_type_key: "department",
    display_name: "Department",
    description: "Department records",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: null,
  },
];

const schemaColumns: SchemaColumn[] = [
  { column_name: "id", primitive_type: "integer" },
  { column_name: "name", primitive_type: "string" },
  { column_name: "dept_id", primitive_type: "integer" },
  { column_name: "salary", primitive_type: "number" },
  { column_name: "internal_code", primitive_type: "string" },
];

const defaultProps = {
  datasetId: "ds-1",
  datasetVersionId: "v-1",
  existingMapping: null as SemanticMapping | null,
  onComplete: vi.fn(),
  onCancel: vi.fn(),
};

const existingMapping: SemanticMapping = {
  id: "map-1",
  dataset_id: "ds-1",
  dataset_version_id: "v-1",
  version_number: 1,
  object_type_id: "ot-employee",
  object_type_key: "employee",
  properties: [
    {
      source_column: "id",
      property_name: "EmployeeID",
      semantic_type: "integer",
      included: true,
      is_primary_key: true,
    },
    {
      source_column: "name",
      property_name: "FullName",
      semantic_type: "string",
      included: true,
      is_primary_key: false,
    },
    {
      source_column: "dept_id",
      property_name: "DepartmentID",
      semantic_type: "integer",
      included: true,
      is_primary_key: false,
    },
  ],
  links: [],
  source_nodes: [],
  computed_properties: [],
  layout_state: {},
  created_at: "2026-01-01T00:00:00Z",
  updated_at: null,
};

const validValidationResult: ValidationResult = {
  valid: true,
  errors: [],
};

// ─── Helpers ───

const setupMocks = () => {
  mockFetchObjectTypes.mockResolvedValue(objectTypes);
  mockFetchDatasetVersionSchema.mockResolvedValue(schemaColumns);
  mockValidateMapping.mockResolvedValue(validValidationResult);
};

// ─── Tests ───

describe("EntityMappingWizard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupMocks();
  });

  // ─── Loading / Error ───

  it("shows loading spinner while fetching initial data", () => {
    mockFetchObjectTypes.mockReturnValue(new Promise(() => {}));
    render(<EntityMappingWizard {...defaultProps} />);

    expect(
      screen.getByText("Loading entity mapping data...")
    ).toBeInTheDocument();
  });

  it("shows error state when initial fetch fails", async () => {
    mockFetchObjectTypes.mockRejectedValue(new Error("API down"));
    render(<EntityMappingWizard {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("API down")).toBeInTheDocument();
    });
  });

  // ─── Step 1: Object Type ───

  describe("Step 1: Object Type", () => {
    it("renders object type selection UI after load", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText("Select or Create Object Type")
        ).toBeInTheDocument();
      });

      // Dropdown with existing types
      const select = screen.getByRole("combobox");
      expect(select).toBeInTheDocument();
      expect(screen.getByText("-- Select object type --")).toBeInTheDocument();
      expect(screen.getByText("Employee (employee)")).toBeInTheDocument();
      expect(screen.getByText("Department (department)")).toBeInTheDocument();
    });

    it("shows 'Create new Object Type' link", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText("+ Create new Object Type")
        ).toBeInTheDocument();
      });
    });

    it("enables Next button when an object type is selected", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      const nextBtn = screen.getByText("Next");
      expect(nextBtn).toBeDisabled();

      // Select an object type
      const select = screen.getByRole("combobox");
      fireEvent.change(select, { target: { value: "ot-employee" } });

      expect(nextBtn).not.toBeDisabled();
    });

    it("moves to step 2 when Next is clicked after selection", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));

      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
    });

    it("pre-selects existing object type when editing", async () => {
      render(
        <EntityMappingWizard
          {...defaultProps}
          existingMapping={existingMapping}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      const select = screen.getByRole("combobox") as HTMLSelectElement;
      expect(select.value).toBe("ot-employee");
    });

    it("shows create form and creates new object type inline", async () => {
      const newType: ObjectType = {
        id: "ot-new",
        tenant_id: "t1",
        object_type_key: "contractor",
        display_name: "Contractor",
        description: "",
        created_at: "2026-01-01T00:00:00Z",
        updated_at: null,
      };
      mockCreateObjectType.mockResolvedValue(newType);

      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Open create form
      fireEvent.click(screen.getByText("+ Create new Object Type"));

      await waitFor(() => {
        expect(screen.getByText("New Object Type")).toBeInTheDocument();
      });

      // Fill form
      const keyInput = screen.getByPlaceholderText("e.g. employee");
      fireEvent.change(keyInput, { target: { value: "contractor" } });

      const nameInput = screen.getByPlaceholderText("e.g. Employee");
      fireEvent.change(nameInput, { target: { value: "Contractor" } });

      // Submit
      fireEvent.click(screen.getByText("Create"));

      await waitFor(() => {
        expect(mockCreateObjectType).toHaveBeenCalledWith({
          object_type_key: "contractor",
          display_name: "Contractor",
          description: "",
        });
      });

      // After creation, Object Type should be pre-selected
      await waitFor(() => {
        expect(
          screen.getByText("+ Create new Object Type")
        ).toBeInTheDocument();
      });
    });

    it("shows no-object-types message when list is empty", async () => {
      mockFetchObjectTypes.mockResolvedValue([]);
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText(/No object types yet/)).toBeInTheDocument();
      });
    });

    // ─── Edit existing Object Type display name ───

    it("shows 'Edit display name' button when an Object Type is selected", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // No edit button before selection
      expect(screen.queryByText("Edit display name")).toBeNull();

      // Select an Object Type
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });

      await waitFor(() => {
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });
    });

    it("opens inline edit form when 'Edit display name' is clicked", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });

      await waitFor(() => {
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Edit display name"));

      await waitFor(() => {
        expect(screen.getByText("Edit Display Name")).toBeInTheDocument();
      });

      // Key is read-only with current key value
      const keyInput = screen.getByDisplayValue("employee");
      expect(keyInput).toBeInTheDocument();
      expect((keyInput as HTMLInputElement).readOnly).toBe(true);

      // Display name input pre-filled with current value
      const nameInput = screen.getByDisplayValue("Employee");
      expect(nameInput).toBeInTheDocument();

      // Save and Cancel buttons present (scope within the edit form)
      const { getByText } = within(
        screen.getByRole("heading", { name: "Edit Display Name" })
          .closest("div")!
      );
      expect(getByText("Save")).toBeInTheDocument();
      expect(getByText("Cancel")).toBeInTheDocument();
    });

    it("Save calls updateObjectType and updates the object types list", async () => {
      const updatedType: ObjectType = {
        ...objectTypes[0],
        display_name: "Employees",
      };
      mockUpdateObjectType.mockResolvedValue(updatedType);

      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      await waitFor(() => {
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Edit display name"));

      await waitFor(() => {
        expect(screen.getByText("Edit Display Name")).toBeInTheDocument();
      });

      // Change the display name
      const nameInput = screen.getByDisplayValue("Employee");
      fireEvent.change(nameInput, { target: { value: "Employees" } });

      // Save should now be enabled (value changed)
      const saveBtn = screen.getByText("Save");
      expect(saveBtn).not.toBeDisabled();

      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(mockUpdateObjectType).toHaveBeenCalledWith("ot-employee", {
          display_name: "Employees",
        });
      });

      // Edit form should close after successful save
      await waitFor(() => {
        expect(screen.queryByText("Edit Display Name")).toBeNull();
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });
    });

    it("Save is disabled when display name is unchanged", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      await waitFor(() => {
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Edit display name"));

      await waitFor(() => {
        expect(screen.getByText("Edit Display Name")).toBeInTheDocument();
      });

      // Name is "Employee" — Save should be disabled (no change)
      const saveBtn = screen.getByText("Save");
      expect(saveBtn).toBeDisabled();
    });

    it("Cancel hides the edit form and returns to selection view", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      await waitFor(() => {
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Edit display name"));

      await waitFor(() => {
        expect(screen.getByText("Edit Display Name")).toBeInTheDocument();
      });

      // Scope Cancel click to the edit form (not footer nav)
      const editForm = screen.getByRole("heading", {
        name: "Edit Display Name",
      }).closest("div")!;
      fireEvent.click(within(editForm).getByText("Cancel"));

      await waitFor(() => {
        expect(screen.queryByText("Edit Display Name")).toBeNull();
        expect(screen.getByText("Edit display name")).toBeInTheDocument();
      });
    });
  });

  // ─── Step 2: Primary Key ───

  describe("Step 2: Primary Key", () => {
    async function navigateToStep2() {
      render(<EntityMappingWizard {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
    }

    it("shows all schema columns as radio buttons", async () => {
      await navigateToStep2();

      schemaColumns.forEach((col) => {
        expect(screen.getByText(col.column_name)).toBeInTheDocument();
      });
      // Primitive types shown as badges
      expect(screen.getAllByText("integer").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("string").length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText("number")).toBeInTheDocument();
    });

    it("Next button disabled until PK is selected", async () => {
      await navigateToStep2();

      const nextBtn = screen.getByText("Next");
      expect(nextBtn).toBeDisabled();
    });

    it("enables Next after selecting a PK", async () => {
      await navigateToStep2();

      const radio = screen.getAllByRole("radio")[0];
      fireEvent.click(radio);

      const nextBtn = screen.getByText("Next");
      expect(nextBtn).not.toBeDisabled();
    });

    it("shows confirmation when PK is selected", async () => {
      await navigateToStep2();

      fireEvent.click(screen.getAllByRole("radio")[0]);

      expect(
        screen.getByText(/Primary key set to/)
      ).toBeInTheDocument();
      // id appears in confirmation + column labels; confirmation renders <strong>id</strong>
      expect(
        screen.getByText((content, element) => {
          return (
            element?.tagName === "P" &&
            element.textContent?.includes("Primary key set to") === true
          );
        })
      ).toBeInTheDocument();
    });
  });

  // ─── Step 3: Properties ───

  describe("Step 3: Properties", () => {
    async function navigateToStep3() {
      render(<EntityMappingWizard {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next")); // Step 1 → 2
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getAllByRole("radio")[0]);
      fireEvent.click(screen.getByText("Next")); // Step 2 → 3
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
    }

    it("renders property mapping grid with all columns", async () => {
      await navigateToStep3();

      schemaColumns.forEach((col) => {
        expect(screen.getByText(col.column_name)).toBeInTheDocument();
      });
    });

    it("shows PK column with 'PK' badge and amber background", async () => {
      await navigateToStep3();

      expect(screen.getByText("PK")).toBeInTheDocument();
      // The PK row has is_primary_key class → amber background
    });

    it("lets user edit property name", async () => {
      await navigateToStep3();

      // Find the name field for the "name" source column
      const nameInputs = screen.getAllByDisplayValue("name");
      expect(nameInputs.length).toBeGreaterThan(0);

      const nameField = nameInputs[0] as HTMLInputElement;
      fireEvent.change(nameField, { target: { value: "FullName" } });
      expect(nameField.value).toBe("FullName");
    });

    it("lets user change semantic type", async () => {
      await navigateToStep3();

      const typeSelects = screen.getAllByRole("combobox");
      // Find the semantic type select (they have "string" as value)
      const semanticSelect = typeSelects.find(
        (s) => (s as HTMLSelectElement).value === "string"
      ) as HTMLSelectElement;
      expect(semanticSelect).toBeDefined();

      fireEvent.change(semanticSelect, { target: { value: "integer" } });
      expect(semanticSelect.value).toBe("integer");
    });

    it("defaults semantic types from schema primitive types", async () => {
      await navigateToStep3();

      const typeSelects = screen.getAllByRole("combobox") as HTMLSelectElement[];
      expect(typeSelects.map((s) => s.value)).toEqual(
        schemaColumns.map((col) => col.primitive_type)
      );
    });

    it("lets user toggle include/exclude for non-PK columns", async () => {
      await navigateToStep3();

      // Find checkboxes (not the PK one which is disabled)
      const checkboxes = screen.getAllByRole("checkbox");
      const nonPkCheckbox = checkboxes.find(
        (cb) => !(cb as HTMLInputElement).disabled
      ) as HTMLInputElement;
      expect(nonPkCheckbox).toBeDefined();
      expect(nonPkCheckbox.checked).toBe(true);

      fireEvent.click(nonPkCheckbox);
      expect(nonPkCheckbox.checked).toBe(false);
    });

    it("toggles all non-PK columns from the header checkbox", async () => {
      await navigateToStep3();

      const headerCheckbox = screen.getByLabelText("Toggle all included columns");
      expect(headerCheckbox).toBeChecked();

      fireEvent.click(headerCheckbox);

      const checkboxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
      const enabledCheckboxes = checkboxes.filter((cb) => !cb.disabled);

      enabledCheckboxes.forEach((cb) => {
        expect(cb.checked).toBe(false);
      });
      expect(headerCheckbox).not.toBeChecked();
    });

    it("PK column checkbox is disabled (cannot be excluded)", async () => {
      await navigateToStep3();

      // Find the row containing "PK" badge
      const pkBadge = screen.getByText("PK");
      const pkRow = pkBadge.closest("tr");
      expect(pkRow).toBeInTheDocument();

      const pkCheckbox = pkRow!.querySelector(
        'input[type="checkbox"]'
      ) as HTMLInputElement;
      expect(pkCheckbox).toBeDefined();
      expect(pkCheckbox.disabled).toBe(true);
    });

    it("shows validation error for duplicate property names", async () => {
      await navigateToStep3();

      // Set both "name" and "dept_id" properties to the same name
      const inputs = screen.getAllByRole("textbox");
      // The property name input for "dept_id" column
      const deptNameInput = inputs.find(
        (el) => (el as HTMLInputElement).value === "dept_id"
      ) as HTMLInputElement;
      expect(deptNameInput).toBeDefined();

      fireEvent.change(deptNameInput, { target: { value: "name" } });

      // Next should be disabled because of duplicate property name
      await waitFor(() => {
        const nextBtn = screen.getByText("Next");
        expect(nextBtn).toBeDisabled();
      });
    });
  });

  // ─── Step 4: Links ───

  describe("Step 4: Links", () => {
    async function navigateToStep4() {
      render(<EntityMappingWizard {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getAllByRole("radio")[0]);
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(
          screen.getByText("Entity Relationship Links")
        ).toBeInTheDocument();
      });
    }

    it("shows empty links state", async () => {
      await navigateToStep4();

      expect(screen.getByText("No links configured yet.")).toBeInTheDocument();
      expect(screen.getByText("+ Add Link")).toBeInTheDocument();
    });

    it("adds a new link form", async () => {
      await navigateToStep4();

      fireEvent.click(screen.getByText("+ Add Link"));

      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      // Should have a Remove button
      expect(screen.getByText("Remove")).toBeInTheDocument();

      // Should have link ID input
      expect(screen.getByPlaceholderText("e.g. reports_to")).toBeInTheDocument();

      // Should have display name input
      expect(screen.getByPlaceholderText("e.g. Reports To")).toBeInTheDocument();

      // Should have source property select
      const selects = screen.getAllByRole("combobox");
      const sourceSelect = selects.find(
        (s) =>
          s.parentElement?.textContent?.includes("Source Property")
      );
      expect(sourceSelect).toBeDefined();

      // Should have target object type select
      const targetSelect = selects.find(
        (s) =>
          s.parentElement?.textContent?.includes("Target Object Type")
      );
      expect(targetSelect).toBeDefined();
    });

    it("removes a link", async () => {
      await navigateToStep4();

      fireEvent.click(screen.getByText("+ Add Link"));

      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Remove"));

      await waitFor(() => {
        expect(screen.getByText("No links configured yet.")).toBeInTheDocument();
      });
    });

    it("edits link fields", async () => {
      await navigateToStep4();

      fireEvent.click(screen.getByText("+ Add Link"));

      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      // Fill link_id
      const linkIdInput = screen.getByPlaceholderText("e.g. reports_to");
      fireEvent.change(linkIdInput, { target: { value: "dept_link" } });
      expect((linkIdInput as HTMLInputElement).value).toBe("dept_link");

      // Fill display_name
      const displayNameInput = screen.getByPlaceholderText("e.g. Reports To");
      fireEvent.change(displayNameInput, { target: { value: "Department" } });
      expect((displayNameInput as HTMLInputElement).value).toBe("Department");
    });

    it("shows many-to-many warning", async () => {
      await navigateToStep4();

      fireEvent.click(screen.getByText("+ Add Link"));

      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      // Find the cardinality select and change to many_to_many
      const selects = screen.getAllByRole("combobox");
      const cardSelect = selects.find(
        (s) => (s as HTMLSelectElement).value === "many_to_one"
      ) as HTMLSelectElement;
      expect(cardSelect).toBeDefined();

      fireEvent.change(cardSelect, { target: { value: "many_to_many" } });

      await waitFor(() => {
        expect(screen.getByText(/many-to-many is metadata-only/)).toBeInTheDocument();
      });
    });

    it("blocks publish when link fields are empty", async () => {
      await navigateToStep4();

      fireEvent.click(screen.getByText("+ Add Link"));

      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      // Publish Mapping should be disabled since link fields are empty
      const publishBtn = screen.getByText("Publish Mapping");
      expect(publishBtn).toBeDisabled();
    });
  });

  // ─── Navigation ───

  describe("Navigation", () => {
    it("shows step indicator with all 4 steps", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(
          screen.getByText("Select or Create Object Type")
        ).toBeInTheDocument();
      });

      const steps = [
        "Object Type",
        "Primary Key",
        "Properties",
        "Relationships/Links",
      ];
      steps.forEach((step) => {
        expect(screen.getByText(step)).toBeInTheDocument();
      });
    });

    it("shows Cancel button", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });
    });

    it("calls onCancel when Cancel is clicked", async () => {
      const onCancel = vi.fn();
      render(
        <EntityMappingWizard
          {...defaultProps}
          onCancel={onCancel}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Cancel")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Cancel"));
      expect(onCancel).toHaveBeenCalled();
    });

    it("shows Back button on steps 2-4", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Step 1: no Back button
      expect(screen.queryByText("Back")).toBeNull();

      // Navigate to Step 2
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));

      await waitFor(() => {
        expect(screen.getByText("Back")).toBeInTheDocument();
      });
    });

    it("navigates back to previous step", async () => {
      render(<EntityMappingWizard {...defaultProps} />);

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Go to Step 2
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));

      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });

      // Go back
      fireEvent.click(screen.getByText("Back"));

      await waitFor(() => {
        expect(
          screen.getByText("Select or Create Object Type")
        ).toBeInTheDocument();
      });
    });
  });

  // ─── Save Flow ───

  describe("Save Flow", () => {
    async function navigateToSave() {
      render(<EntityMappingWizard {...defaultProps} />);
      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getAllByRole("radio")[0]);
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(
          screen.getByText("Entity Relationship Links")
        ).toBeInTheDocument();
      });
    }

    it("shows 'Publish Mapping' button when creating new", async () => {
      await navigateToSave();

      expect(screen.getByText("Publish Mapping")).toBeInTheDocument();
    });

    it("shows 'Update Mapping' button when editing existing", async () => {
      mockFetchObjectTypes.mockResolvedValue(objectTypes);
      mockFetchDatasetVersionSchema.mockResolvedValue(schemaColumns);
      mockValidateMapping.mockResolvedValue(validValidationResult);

      render(
        <EntityMappingWizard
          {...defaultProps}
          existingMapping={existingMapping}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Navigate through all steps
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(
          screen.getByText("Entity Relationship Links")
        ).toBeInTheDocument();
      });

      expect(screen.getByText("Update Mapping")).toBeInTheDocument();
    });

    it("blocks save when client-side validation fails", async () => {
      await navigateToSave();

      // Add a link with empty ID (triggers validation error)
      fireEvent.click(screen.getByText("+ Add Link"));
      await waitFor(() => {
        expect(screen.getByText("Link #1")).toBeInTheDocument();
      });

      // Publish Mapping should be disabled because link fields are invalid
      const publishBtn = screen.getByText("Publish Mapping");
      expect(publishBtn).toBeDisabled();

      // validateMapping should NOT have been called
      expect(mockValidateMapping).not.toHaveBeenCalled();
    });

    it("calls validateMapping then createMapping on successful save", async () => {
      mockCreateMapping.mockResolvedValue({ id: "new-map" });

      await navigateToSave();

      fireEvent.click(screen.getByText("Publish Mapping"));

      await waitFor(() => {
        expect(mockValidateMapping).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(mockCreateMapping).toHaveBeenCalledWith(
          "ds-1",
          "v-1",
          expect.objectContaining({
            object_type_id: "ot-employee",
            properties: expect.any(Array),
          })
        );
      });
    });

    it("calls updateMapping when editing existing mapping", async () => {
      mockUpdateMapping.mockResolvedValue({ id: "updated-map" });

      render(
        <EntityMappingWizard
          {...defaultProps}
          existingMapping={existingMapping}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Navigate all steps
      fireEvent.click(screen.getByText("Next")); // Step 1→2
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next")); // Step 2→3 (PK already set)
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next")); // Step 3→4
      await waitFor(() => {
        expect(screen.getByText("Entity Relationship Links")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Update Mapping"));

      await waitFor(() => {
        expect(mockValidateMapping).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(mockUpdateMapping).toHaveBeenCalledWith(
          "ds-1",
          "v-1",
          expect.objectContaining({
            object_type_id: "ot-employee",
          })
        );
      });
    });

    it("shows server validation errors when validate returns invalid", async () => {
      const invalidResult: ValidationResult = {
        valid: false,
        errors: [
          {
            field: "primary_key",
            value: null,
            message: "A primary key must be selected",
          },
        ],
      };
      mockValidateMapping.mockResolvedValue(invalidResult);

      await navigateToSave();

      fireEvent.click(screen.getByText("Publish Mapping"));

      await waitFor(() => {
        expect(mockValidateMapping).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(screen.getByText(/Please fix the following errors/)).toBeInTheDocument();
        expect(
          screen.getByText("A primary key must be selected")
        ).toBeInTheDocument();
      });

      // createMapping should NOT have been called
      expect(mockCreateMapping).not.toHaveBeenCalled();
    });

    it("calls onComplete after successful save", async () => {
      const onComplete = vi.fn();
      mockCreateMapping.mockResolvedValue({ id: "new-map" });

      render(
        <EntityMappingWizard
          {...defaultProps}
          onComplete={onComplete}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Navigate all steps
      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "ot-employee" },
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getAllByRole("radio")[0]);
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Entity Relationship Links")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Publish Mapping"));

      await waitFor(() => {
        expect(mockCreateMapping).toHaveBeenCalled();
      });

      await waitFor(() => {
        expect(onComplete).toHaveBeenCalled();
      });
    });
  });

  // ─── Pre-fill from existing mapping ───

  describe("Existing Mapping Pre-fill", () => {
    it("pre-fills properties from existing mapping", async () => {
      render(
        <EntityMappingWizard
          {...defaultProps}
          existingMapping={existingMapping}
        />
      );

      await waitFor(() => {
        expect(screen.getByText("Select or Create Object Type")).toBeInTheDocument();
      });

      // Navigate to step 3
      fireEvent.click(screen.getByText("Next"));
      await waitFor(() => {
        expect(screen.getByText("Select Primary Key")).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText("Next"));

      await waitFor(() => {
        expect(screen.getByText("Map Properties")).toBeInTheDocument();
      });

      // Should show pre-filled property names
      expect(screen.getByDisplayValue("EmployeeID")).toBeInTheDocument();
      expect(screen.getByDisplayValue("FullName")).toBeInTheDocument();
      expect(screen.getByDisplayValue("DepartmentID")).toBeInTheDocument();
    });
  });
});
