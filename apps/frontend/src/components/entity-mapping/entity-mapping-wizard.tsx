"use client";

import { useCallback, useEffect, useState } from "react";
import {
  fetchObjectTypes,
  createObjectType,
  fetchDatasetVersionSchema,
  createMapping,
  updateMapping,
  validateMapping,
} from "@/lib/api/semantic";
import type {
  ObjectType,
  SchemaColumn,
  PropertyMapping,
  SemanticMapping,
} from "@/lib/api/types";
import { LoadingSpinner, ErrorState, useToast } from "@/components/shared";

type Step = 1 | 2 | 3;

type Props = {
  datasetId: string;
  datasetVersionId: string;
  existingMapping: SemanticMapping | null;
  onComplete: () => void;
  onCancel: () => void;
};

export const EntityMappingWizard = ({
  datasetId,
  datasetVersionId,
  existingMapping,
  onComplete,
  onCancel,
}: Props) => {
  const toast = useToast();
  const [step, setStep] = useState<Step>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Record<string, string>
  >({});

  // ─── Shared state ───
  const [schemaColumns, setSchemaColumns] = useState<SchemaColumn[]>([]);
  const [objectTypes, setObjectTypes] = useState<ObjectType[]>([]);
  const [selectedObjectTypeId, setSelectedObjectTypeId] = useState<string>(
    existingMapping?.object_type_id ?? ""
  );
  const [selectedObjectTypeKey, setSelectedObjectTypeKey] = useState<string>(
    existingMapping?.object_type_key ?? ""
  );

  // ─── Create Object Type form (Step 1) ───
  const [newTypeKey, setNewTypeKey] = useState("");
  const [newTypeDisplayName, setNewTypeDisplayName] = useState("");
  const [newTypeDescription, setNewTypeDescription] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [creatingType, setCreatingType] = useState(false);

  // ─── Property mappings (Steps 2 & 3) ───
  const [properties, setProperties] = useState<PropertyMapping[]>([]);
  const [primaryKeyColumn, setPrimaryKeyColumn] = useState<string>("");

  // ─── Initial load ───
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [types, schema] = await Promise.all([
          fetchObjectTypes(),
          fetchDatasetVersionSchema(datasetId, datasetVersionId),
        ]);
        setObjectTypes(types);
        setSchemaColumns(schema);

        // Initialize property mappings from existing or from schema
        if (existingMapping) {
          setProperties(existingMapping.properties);
          const pkProp = existingMapping.properties.find(
            (p) => p.is_primary_key
          );
          if (pkProp) {
            setPrimaryKeyColumn(pkProp.source_column);
          }
        } else {
          // Initialize from schema: all columns included, default to string type
          setProperties(
            schema.map((col) => ({
              source_column: col.column_name,
              property_name: col.column_name,
              semantic_type: "string",
              included: true,
              is_primary_key: false,
            }))
          );
        }
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load data"
        );
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [datasetId, datasetVersionId, existingMapping]);

  // Normalize property name (trim + lowercase)
  const normalizeName = (name: string): string =>
    name.trim().toLowerCase();

  // ─── Client-side validation ───
  const getPropertyErrors = useCallback((): Record<string, string> => {
    const errs: Record<string, string> = {};

    // Check PK is selected (Step 2)
    if (!primaryKeyColumn) {
      errs["primary_key"] = "Select a primary key column";
    }

    // Check property name uniqueness (Step 3)
    const normalizedNames = new Map<string, number>();
    properties.forEach((p, idx) => {
      if (!p.included) return; // skip excluded
      const norm = normalizeName(p.property_name);
      if (!norm) {
        errs[`prop_${idx}_name`] = "Property name must not be empty";
        return;
      }
      const existing = normalizedNames.get(norm);
      if (existing !== undefined) {
        errs[`prop_${idx}_name`] = `Duplicate: "${p.property_name}" matches "${properties[existing].property_name}"`;
        errs[`prop_${existing}_name`] = `Duplicate: "${properties[existing].property_name}" matches "${p.property_name}"`;
      } else {
        normalizedNames.set(norm, idx);
      }
    });

    return errs;
  }, [primaryKeyColumn, properties]);

  // ─── Step navigation ───
  const canGoNext = (): boolean => {
    const errs = getPropertyErrors();
    if (step === 1) {
      return !!selectedObjectTypeId;
    }
    if (step === 2) {
      return !!primaryKeyColumn;
    }
    return Object.keys(errs).length === 0;
  };

  const handleNext = () => {
    if (step < 3) {
      setStep((step + 1) as Step);
    }
  };

  const handleBack = () => {
    if (step > 1) {
      setStep((step - 1) as Step);
    }
  };

  // ─── Create Object Type ───
  const handleCreateObjectType = async () => {
    if (!newTypeKey || !newTypeDisplayName) return;
    setCreatingType(true);
    try {
      const newType = await createObjectType({
        object_type_key: newTypeKey,
        display_name: newTypeDisplayName,
        description: newTypeDescription,
      });
      setObjectTypes((prev) => [newType, ...prev]);
      setSelectedObjectTypeId(newType.id);
      setSelectedObjectTypeKey(newType.object_type_key);
      setShowCreateForm(false);
      setNewTypeKey("");
      setNewTypeDisplayName("");
      setNewTypeDescription("");
      toast.success("Object type created", `"${newType.display_name}" created.`);
    } catch (err) {
      toast.danger(
        "Failed to create",
        err instanceof Error ? err.message : "Unknown error"
      );
    } finally {
      setCreatingType(false);
    }
  };

  // ─── Property change handlers ───
  const handlePropertyChange = (
    index: number,
    field: keyof PropertyMapping,
    value: string | boolean
  ) => {
    setProperties((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      return updated;
    });
  };

  const handlePrimaryKeyChange = (columnName: string) => {
    setPrimaryKeyColumn(columnName);
    setProperties((prev) =>
      prev.map((p) => ({
        ...p,
        is_primary_key: p.source_column === columnName,
        // PK must be included
        included: p.source_column === columnName ? true : p.included,
      }))
    );
  };

  const handleToggleInclude = (index: number) => {
    const prop = properties[index];
    // Cannot exclude PK
    if (prop.is_primary_key) return;
    setProperties((prev) => {
      const updated = [...prev];
      updated[index] = {
        ...updated[index],
        included: !updated[index].included,
      };
      return updated;
    });
  };

  // ─── Save ───
  const handleSave = async () => {
    const errs = getPropertyErrors();
    setValidationErrors(errs);
    if (Object.keys(errs).length > 0) {
      toast.danger("Validation failed", "Fix errors before saving.");
      return;
    }

    setSaving(true);
    try {
      // First validate on server
      const validation = await validateMapping(datasetId, datasetVersionId, {
        object_type_id: selectedObjectTypeId,
        object_type_key: selectedObjectTypeKey,
        properties,
      });

      if (!validation.valid) {
        const serverErrors: Record<string, string> = {};
        validation.errors.forEach((e) => {
          serverErrors[e.field] = e.message;
        });
        setValidationErrors(serverErrors);
        toast.danger(
          "Server validation failed",
          `${validation.errors.length} error(s) found.`
        );
        return;
      }

      // Save mapping
      if (existingMapping) {
        await updateMapping(datasetId, datasetVersionId, {
          object_type_id: selectedObjectTypeId,
          object_type_key: selectedObjectTypeKey,
          properties,
        });
        toast.success("Mapping updated", "Entity mapping saved.");
      } else {
        await createMapping(datasetId, datasetVersionId, {
          object_type_id: selectedObjectTypeId,
          object_type_key: selectedObjectTypeKey,
          properties,
        });
        toast.success("Mapping created", "Entity mapping published.");
      }
      onComplete();
    } catch (err) {
      toast.danger(
        "Save failed",
        err instanceof Error ? err.message : "Unknown error"
      );
    } finally {
      setSaving(false);
    }
  };

  // ─── Render ───
  if (loading) return <LoadingSpinner text="Loading entity mapping data..." />;
  if (error) return <ErrorState message={error} />;

  const stepLabels = ["Object Type", "Primary Key", "Properties"];

  return (
    <div className="space-y-6">
      {/* Step indicator */}
      <div className="flex items-center gap-2">
        {([1, 2, 3] as const).map((s) => (
          <div key={s} className="flex items-center gap-2">
            <div
              className={`flex size-7 items-center justify-center rounded-full text-xs font-semibold ${
                step === s
                  ? "bg-zinc-900 text-white"
                  : step > s
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-zinc-100 text-zinc-400"
              }`}
            >
              {step > s ? (
                <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                s
              )}
            </div>
            <span
              className={`text-xs font-medium ${
                step === s ? "text-zinc-900" : "text-zinc-400"
              }`}
            >
              {stepLabels[s - 1]}
            </span>
            {s < 3 && (
              <div
                className={`mx-1 h-px w-6 ${
                  step > s ? "bg-emerald-300" : "bg-zinc-200"
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Inline validation errors */}
      {Object.keys(validationErrors).length > 0 && (
        <div className="rounded-md border border-rose-200 bg-rose-50 p-3">
          <p className="text-xs font-medium text-rose-800">
            Please fix the following errors:
          </p>
          <ul className="mt-1 list-inside list-disc text-xs text-rose-700">
            {Object.values(validationErrors).map((msg, i) => (
              <li key={i}>{msg}</li>
            ))}
          </ul>
        </div>
      )}

      {/* ─── Step 1: Select/Create Object Type ─── */}
      {step === 1 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-900">
            Select or Create Object Type
          </h3>
          <p className="text-xs text-zinc-500">
            An Object Type defines the semantic entity for this dataset.
            Choose an existing type or create a new one.
          </p>

          {/* Existing types dropdown */}
          {objectTypes.length > 0 && (
            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Existing Object Types
              </label>
              <select
                value={selectedObjectTypeId}
                onChange={(e) => {
                  const selected = objectTypes.find(
                    (t) => t.id === e.target.value
                  );
                  if (selected) {
                    setSelectedObjectTypeId(selected.id);
                    setSelectedObjectTypeKey(selected.object_type_key);
                  }
                }}
                className="w-full rounded-md border border-zinc-300 px-3 py-2 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              >
                <option value="">-- Select object type --</option>
                {objectTypes.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.display_name} ({t.object_type_key})
                  </option>
                ))}
              </select>
            </div>
          )}

          {objectTypes.length === 0 && !showCreateForm && (
            <p className="text-xs text-zinc-400">
              No object types yet. Create one below.
            </p>
          )}

          {/* Create new inline */}
          {!showCreateForm ? (
            <button
              type="button"
              onClick={() => setShowCreateForm(true)}
              className="text-xs font-medium text-zinc-600 hover:text-zinc-900"
            >
              + Create new Object Type
            </button>
          ) : (
            <div className="space-y-3 rounded-md border border-zinc-200 bg-zinc-50 p-4">
              <h4 className="text-xs font-semibold text-zinc-700">
                New Object Type
              </h4>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Key (lowercase_snake, immutable)
                </label>
                <input
                  type="text"
                  value={newTypeKey}
                  onChange={(e) =>
                    setNewTypeKey(
                      e.target.value
                        .toLowerCase()
                        .replace(/[^a-z0-9_]/g, "_")
                    )
                  }
                  placeholder="e.g. employee"
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Display Name
                </label>
                <input
                  type="text"
                  value={newTypeDisplayName}
                  onChange={(e) => setNewTypeDisplayName(e.target.value)}
                  placeholder="e.g. Employee"
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-zinc-600 mb-1">
                  Description (optional)
                </label>
                <input
                  type="text"
                  value={newTypeDescription}
                  onChange={(e) => setNewTypeDescription(e.target.value)}
                  placeholder="Brief description..."
                  className="w-full rounded-md border border-zinc-300 px-3 py-1.5 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleCreateObjectType}
                  disabled={creatingType || !newTypeKey || !newTypeDisplayName}
                  className="rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {creatingType ? "Creating..." : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-600 hover:bg-zinc-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Step 2: Select Primary Key ─── */}
      {step === 2 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-900">
            Select Primary Key
          </h3>
          <p className="text-xs text-zinc-500">
            Choose the column that uniquely identifies each row. The primary key
            is required and will be automatically included in the mapping.
          </p>

          <div className="grid grid-cols-1 gap-2">
            {schemaColumns.map((col) => (
              <label
                key={col.column_name}
                className={`flex cursor-pointer items-center gap-3 rounded-md border p-3 transition-colors hover:bg-zinc-50 ${
                  primaryKeyColumn === col.column_name
                    ? "border-zinc-900 bg-zinc-50 ring-1 ring-zinc-900"
                    : "border-zinc-200"
                }`}
              >
                <input
                  type="radio"
                  name="primary_key"
                  checked={primaryKeyColumn === col.column_name}
                  onChange={() => handlePrimaryKeyChange(col.column_name)}
                  className="size-4 accent-zinc-900"
                />
                <div className="flex-1">
                  <span className="text-sm font-medium text-zinc-900">
                    {col.column_name}
                  </span>
                  <span className="ml-2 inline-block rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-500">
                    {col.primitive_type}
                  </span>
                </div>
              </label>
            ))}
          </div>

          {schemaColumns.length === 0 && (
            <p className="text-sm text-zinc-400">No columns available.</p>
          )}

          {primaryKeyColumn && (
            <p className="text-xs text-emerald-600">
              Primary key set to <strong>{primaryKeyColumn}</strong>
            </p>
          )}
        </div>
      )}

      {/* ─── Step 3: Property Mapping Grid ─── */}
      {step === 3 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-900">
            Map Properties
          </h3>
          <p className="text-xs text-zinc-500">
            Configure how each column maps to a property. You can rename columns,
            set semantic types, and choose which properties to include.
          </p>

          <div className="overflow-x-auto rounded-md border border-zinc-200">
            <table className="min-w-full divide-y divide-zinc-200 text-sm">
              <thead>
                <tr className="bg-zinc-50">
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Source Column
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Property Name
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Semantic Type
                  </th>
                  <th className="px-3 py-2 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Include
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {properties.map((prop, idx) => {
                  const errKey = `prop_${idx}_name`;
                  const errorMsg = validationErrors[errKey];
                  const schemaCol = schemaColumns.find(
                    (c) => c.column_name === prop.source_column
                  );

                  return (
                    <tr
                      key={prop.source_column}
                      className={`hover:bg-zinc-50 ${
                        prop.is_primary_key ? "bg-amber-50/50" : ""
                      }`}
                    >
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`font-medium ${
                              prop.is_primary_key
                                ? "text-amber-800"
                                : "text-zinc-900"
                            }`}
                          >
                            {prop.source_column}
                          </span>
                          {prop.is_primary_key && (
                            <span className="inline-block rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-800">
                              PK
                            </span>
                          )}
                          <span className="text-[10px] text-zinc-400">
                            {schemaCol?.primitive_type ?? "?"}
                          </span>
                        </div>
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={prop.property_name}
                          onChange={(e) =>
                            handlePropertyChange(
                              idx,
                              "property_name",
                              e.target.value
                            )
                          }
                          className={`w-full rounded border px-2 py-1 text-sm focus:outline-none focus:ring-1 ${
                            errorMsg
                              ? "border-rose-300 focus:border-rose-500 focus:ring-rose-500"
                              : "border-zinc-200 focus:border-zinc-500 focus:ring-zinc-500"
                          }`}
                        />
                        {errorMsg && (
                          <p className="mt-0.5 text-[10px] text-rose-600">
                            {errorMsg}
                          </p>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={prop.semantic_type}
                          onChange={(e) =>
                            handlePropertyChange(
                              idx,
                              "semantic_type",
                              e.target.value
                            )
                          }
                          className="rounded border border-zinc-200 px-2 py-1 text-sm focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
                        >
                          <option value="string">string</option>
                          <option value="integer">integer</option>
                          <option value="number">number</option>
                          <option value="boolean">boolean</option>
                          <option value="datetime">datetime</option>
                          <option value="date">date</option>
                        </select>
                      </td>
                      <td className="px-3 py-2 text-center">
                        <input
                          type="checkbox"
                          checked={prop.included}
                          onChange={() => handleToggleInclude(idx)}
                          disabled={prop.is_primary_key}
                          className="size-4 accent-zinc-900 disabled:opacity-50"
                          title={
                            prop.is_primary_key
                              ? "Primary key must be included"
                              : "Toggle inclusion"
                          }
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── Navigation buttons ─── */}
      <div className="flex items-center justify-between border-t border-zinc-200 pt-4">
        <div className="flex gap-2">
          {step > 1 && (
            <button
              type="button"
              onClick={handleBack}
              className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
            >
              Back
            </button>
          )}
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-zinc-200 bg-white px-4 py-2 text-sm font-medium text-zinc-500 transition-colors hover:bg-zinc-50"
          >
            Cancel
          </button>
        </div>

        <div>
          {step < 3 ? (
            <button
              type="button"
              onClick={handleNext}
              disabled={!canGoNext()}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || !canGoNext()}
              className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Saving..." : existingMapping ? "Update Mapping" : "Publish Mapping"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
