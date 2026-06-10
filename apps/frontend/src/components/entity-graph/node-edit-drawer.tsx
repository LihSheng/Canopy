"use client";

import { useState } from "react";
import { ComputedPropertyComposer, type EntityComputedProperty } from "./computed-property-composer";

type FieldRef = {
  source_id: string;
  source_name: string;
  field_name: string;
};

type ComputedProperty = {
  id: string;
  property_name: string;
  semantic_type: string;
  composition_kind: string;
  expression: string;
  inputs: FieldRef[];
  included: boolean;
};

type Property = {
  source_column: string;
  property_name: string;
  semantic_type: string;
  included: boolean;
  is_primary_key: boolean;
};

type LinkInfo = {
  link_id: string;
  source_property_key: string;
  target_property_key: string;
  cardinality: string;
};

type EntityLinkShape = {
  link_id: string;
  display_name: string;
  source_property_key: string;
  target_object_type_id: string;
  target_property_key: string;
  cardinality: string;
};

type ObjectTypeOption = {
  id: string;
  display_name: string;
  object_type_key: string;
};

type SourceNodeData = {
  source_id: string;
  name: string;
  source_type: string;
  fields: string[];
};

type NodeData = {
  label: string;
  nodeType?: "entity" | "source" | "dataset" | "target";
  properties?: Property[];
  computedProperties?: ComputedProperty[];
  sourceType?: string;
  fields?: string[];
  linkInfo?: LinkInfo;
};

export type SelectedNode = {
  id: string;
  type: string;
  data: NodeData;
};

type Props = {
  node: SelectedNode;
  sourceNodes?: SourceNodeData[];
  entityId?: string;
  onClose: () => void;
  onUpdateProperties?: (properties: Property[]) => void;
  onUpdateComputedProperties?: (computedProperties: ComputedProperty[]) => void;
  links?: EntityLinkShape[];
  onUpdateLinks?: (links: EntityLinkShape[]) => void;
  objectTypes?: ObjectTypeOption[];
};

const SEMANTIC_TYPES = ["string", "integer", "number", "boolean", "datetime", "date"];

export const NodeEditDrawer = ({
  node,
  sourceNodes,
  entityId,
  onClose,
  onUpdateProperties,
  onUpdateComputedProperties,
  links,
  onUpdateLinks,
  objectTypes,
}: Props) => {
  const data = node.data;
  const isEntity = data.nodeType === "entity";
  const isReadOnly = data.nodeType === "source" || data.nodeType === "dataset";
  const isTarget = data.nodeType === "target";
  const [editedProperties, setEditedProperties] = useState<Property[] | null>(null);
  const [showFieldMapper, setShowFieldMapper] = useState(false);
  const [showComposer, setShowComposer] = useState(false);
  const [newPropSourceColumn, setNewPropSourceColumn] = useState("");
  const [newPropName, setNewPropName] = useState("");
  const [newPropType, setNewPropType] = useState("string");
  const [newPropPK, setNewPropPK] = useState(false);

  const properties = editedProperties ?? data.properties ?? [];

  const toggleIncluded = (idx: number) => {
    if (!isEntity) return;
    const updated = properties.map((p, i) =>
      i === idx ? { ...p, included: !p.included } : p
    );
    setEditedProperties(updated);
    onUpdateProperties?.(updated);
  };

  // Collect all fields from connected source nodes
  const allSourceFields: { fieldName: string; sourceName: string }[] = [];
  (sourceNodes || []).forEach((sn) => {
    (sn.fields || []).forEach((field) => {
      allSourceFields.push({ fieldName: field, sourceName: sn.name });
    });
  });

  // Fields already mapped to properties
  const mappedColumns = new Set(properties.map((p) => p.source_column));
  const unmappedFields = allSourceFields.filter(
    (sf) => !mappedColumns.has(sf.fieldName)
  );

  const handleCreateProperty = () => {
    const trimmedCol = newPropSourceColumn.trim();
    const trimmedName = newPropName.trim();
    if (!trimmedCol || !trimmedName) return;

    const newProp: Property = {
      source_column: trimmedCol,
      property_name: trimmedName,
      semantic_type: newPropType,
      included: true,
      is_primary_key: newPropPK,
    };
    const updated = [...properties, newProp];
    setEditedProperties(updated);
    onUpdateProperties?.(updated);

    // Reset form
    setNewPropSourceColumn("");
    setNewPropName("");
    setNewPropType("string");
    setNewPropPK(false);
  };

  const handleRemoveProperty = (idx: number) => {
    const updated = properties.filter((_, i) => i !== idx);
    setEditedProperties(updated);
    onUpdateProperties?.(updated);
  };

  const handleSetPrimaryKey = (idx: number) => {
    if (!isEntity) return;
    const updated = properties.map((p, i) => ({
      ...p,
      is_primary_key: i === idx,
      included: i === idx ? true : p.included,
    }));
    setEditedProperties(updated);
    onUpdateProperties?.(updated);
  };

  const handleAddComputedProperty = (cp: EntityComputedProperty) => {
    const current = data.computedProperties || [];
    // Bridge new EntityComputedProperty to old ComputedProperty shape for legacy consumers
    const legacyCp: ComputedProperty = {
      id: cp.id,
      property_name: cp.property_key,
      semantic_type: cp.output_type,
      composition_kind: cp.formula_type,
      expression: cp.formula,
      inputs: [],
      included: cp.is_active,
    };
    const updated = [...current, legacyCp];
    onUpdateComputedProperties?.(updated);
    setShowComposer(false);
  };

  const handleRemoveComputedProperty = (idx: number) => {
    const current = data.computedProperties || [];
    const updated = current.filter((_, i) => i !== idx);
    onUpdateComputedProperties?.(updated);
  };

  // ─── Link editing (entity node only) ───
  const [editedLinks, setEditedLinks] = useState<EntityLinkShape[] | null>(null);
  const currentLinks = editedLinks ?? links ?? [];

  const handleLinkChange = (idx: number, field: keyof EntityLinkShape, value: string) => {
    const updated = currentLinks.map((ln, i) =>
      i === idx ? { ...ln, [field]: value } : ln
    );
    setEditedLinks(updated);
    onUpdateLinks?.(updated);
  };

  const handleAddLink = () => {
    const updated = [
      ...currentLinks,
      {
        link_id: "",
        display_name: "",
        source_property_key: "",
        target_object_type_id: "",
        target_property_key: "",
        cardinality: "many_to_one",
      },
    ];
    setEditedLinks(updated);
    onUpdateLinks?.(updated);
  };

  const handleRemoveLink = (idx: number) => {
    const updated = currentLinks.filter((_, i) => i !== idx);
    setEditedLinks(updated);
    onUpdateLinks?.(updated);
  };

  const headerLabel = isEntity ? "Entity: "
    : data.nodeType === "source" ? "Source: "
    : isTarget ? "Target: "
    : "Dataset: ";

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-80 border-l border-zinc-200 bg-white shadow-lg overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-zinc-200 p-4">
        <h3 className="text-sm font-semibold text-zinc-900">
          {headerLabel}{data.label}
        </h3>
        <button
          type="button"
          onClick={onClose}
          className="rounded p-1 text-zinc-400 hover:text-zinc-600"
        >
          <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Read-only badge */}
      {isReadOnly && (
        <div className="border-b border-zinc-200 bg-zinc-50 px-4 py-2">
          <span className="inline-block rounded-full border border-zinc-300 bg-zinc-50 px-2.5 py-0.5 text-xs font-medium text-zinc-500">
            Read only
          </span>
        </div>
      )}

      {/* Entity Properties — editable */}
      {isEntity && (
        <div className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Properties ({properties.length})
            </h4>
            <button
              type="button"
              onClick={() => setShowFieldMapper(!showFieldMapper)}
              className="text-xs font-medium text-zinc-500 hover:text-zinc-900"
            >
              {showFieldMapper ? "Hide mapper" : "+ Map field"}
            </button>
          </div>

          {/* Inline field-to-property mapper */}
          {showFieldMapper && (
            <div className="mb-4 rounded border border-blue-200 bg-blue-50 p-3">
              <h5 className="mb-2 text-xs font-semibold text-blue-800">
                Map source field to property
              </h5>
              <div className="space-y-2">
                <div>
                  <label className="block text-xs text-blue-700">Source Field</label>
                  {allSourceFields.length === 0 ? (
                    <p className="mt-1 text-xs text-zinc-400">
                      No source nodes connected. Add source nodes first.
                    </p>
                  ) : (
                    <select
                      value={newPropSourceColumn}
                      onChange={(e) => {
                        setNewPropSourceColumn(e.target.value);
                        if (!newPropName) setNewPropName(e.target.value);
                      }}
                      className="mt-1 w-full rounded border border-blue-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                    >
                      <option value="">-- Select field --</option>
                      {unmappedFields.map((sf) => (
                        <option key={sf.fieldName} value={sf.fieldName}>
                          {sf.fieldName} (from {sf.sourceName})
                        </option>
                      ))}
                      {allSourceFields
                        .filter((sf) => mappedColumns.has(sf.fieldName))
                        .map((sf) => (
                          <option
                            key={sf.fieldName}
                            value={sf.fieldName}
                            disabled
                          >
                            {sf.fieldName} — already mapped
                          </option>
                        ))}
                    </select>
                  )}
                </div>
                <div>
                  <label className="block text-xs text-blue-700">Property Name</label>
                  <input
                    type="text"
                    value={newPropName}
                    onChange={(e) => setNewPropName(e.target.value)}
                    placeholder="e.g. employee_id"
                    className="mt-1 w-full rounded border border-blue-300 px-2 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="block text-xs text-blue-700">Type</label>
                    <select
                      value={newPropType}
                      onChange={(e) => setNewPropType(e.target.value)}
                      className="mt-1 w-full rounded border border-blue-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                    >
                      {SEMANTIC_TYPES.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-end gap-1 pb-0.5">
                    <label className="flex items-center gap-1 text-xs text-blue-700">
                      <input
                        type="checkbox"
                        checked={newPropPK}
                        onChange={(e) => setNewPropPK(e.target.checked)}
                        className="rounded border-blue-300"
                      />
                      PK
                    </label>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleCreateProperty}
                  disabled={!newPropSourceColumn.trim() || !newPropName.trim()}
                  className="w-full rounded bg-blue-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Create Property
                </button>
              </div>
            </div>
          )}

          {properties.length === 0 && !showFieldMapper ? (
            <p className="text-xs text-zinc-500">
              No properties defined yet. Click &quot;+ Map field&quot; to create one from a source field.
            </p>
          ) : (
            <ul className="space-y-2">
              {properties.map((prop, idx) => (
                <li
                  key={idx}
                  className="rounded border border-zinc-200 p-3 text-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-zinc-900">
                      {prop.property_name}
                    </span>
                    <div className="flex items-center gap-1">
                      {prop.is_primary_key && (
                        <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                          PK
                        </span>
                      )}
                      {!prop.is_primary_key && (
                        <button
                          type="button"
                          onClick={() => handleSetPrimaryKey(idx)}
                          title="Set as primary key"
                          className="rounded px-1.5 py-0.5 text-xs text-zinc-400 hover:bg-amber-50 hover:text-amber-700"
                        >
                          PK?
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="mt-1 flex items-center gap-2 text-xs text-zinc-500">
                    <span>{prop.semantic_type}</span>
                    <span>&middot;</span>
                    <span className="text-zinc-400">{prop.source_column}</span>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => toggleIncluded(idx)}
                      className={`rounded px-2 py-0.5 text-xs font-medium transition-colors ${
                        prop.included
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-zinc-100 text-zinc-400"
                      }`}
                    >
                      {prop.included ? "Included" : "Excluded"}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRemoveProperty(idx)}
                      className="rounded px-2 py-0.5 text-xs font-medium text-rose-500 hover:bg-rose-50"
                    >
                      Remove
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* Computed Properties */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Computed Properties ({(data.computedProperties || []).length})
              </h4>
              <button
                type="button"
                onClick={() => setShowComposer(!showComposer)}
                className="text-xs font-medium text-purple-600 hover:text-purple-800"
              >
                {showComposer ? "Hide composer" : "+ Compose property"}
              </button>
            </div>

            {/* Composer form */}
            {showComposer && (
              <div className="mb-4">
                <ComputedPropertyComposer
                  existingPropertyKeys={[
                    ...properties.map((p) => p.property_name),
                    ...(data.computedProperties || []).map((cp) => cp.property_name),
                  ]}
                  entityId={entityId || ""}
                  onAdd={handleAddComputedProperty}
                  onCancel={() => setShowComposer(false)}
                />
              </div>
            )}

            {(data.computedProperties || []).length === 0 && !showComposer ? (
              <p className="text-xs text-zinc-400">
                No computed properties defined. Click &quot;+ Compose property&quot; to create one from multiple source fields.
              </p>
            ) : (
              <ul className="space-y-2">
                {(data.computedProperties || []).map((cp, idx) => (
                  <li
                    key={cp.id || idx}
                    className="rounded border border-purple-200 bg-purple-50 p-3 text-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-zinc-900">
                        {cp.property_name}
                      </span>
                      <div className="flex items-center gap-1">
                        <span className="inline-block rounded-full px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800">
                          {cp.composition_kind}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveComputedProperty(idx)}
                          className="rounded px-1 py-0.5 text-xs text-rose-400 hover:text-rose-600 hover:bg-rose-50"
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                    <div className="mt-1 flex items-center gap-2 text-xs text-zinc-500">
                      <span>{cp.semantic_type}</span>
                      {cp.expression && (
                        <>
                          <span>&middot;</span>
                          <span className="text-zinc-400 font-mono">{cp.expression}</span>
                        </>
                      )}
                    </div>
                    {(cp.inputs || []).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {(cp.inputs || []).map((inp, j) => (
                          <span
                            key={j}
                            className="inline-block rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-700"
                          >
                            {inp.source_name && `${inp.source_name}.`}{inp.field_name}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-2">
                      <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${
                        cp.included
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-zinc-100 text-zinc-400"
                      }`}>
                        {cp.included ? "Included" : "Excluded"}
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
          {/* ─── Entity Links ─── */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Links ({currentLinks.length})
              </h4>
              <button
                type="button"
                onClick={handleAddLink}
                className="text-xs font-medium text-blue-600 hover:text-blue-800"
              >
                + Add Link
              </button>
            </div>

            {currentLinks.length === 0 ? (
              <p className="text-xs text-zinc-400">
                No relationship links defined. Click &quot;+ Add Link&quot; to connect to another entity.
              </p>
            ) : (
              <ul className="space-y-3">
                {currentLinks.map((link, idx) => (
                  <li
                    key={idx}
                    className="rounded border border-blue-200 bg-blue-50 p-3 text-sm"
                  >
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-blue-700">
                        Link #{idx + 1}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleRemoveLink(idx)}
                        className="rounded px-1 py-0.5 text-xs text-rose-400 hover:text-rose-600 hover:bg-rose-50"
                      >
                        Remove
                      </button>
                    </div>
                    <div className="space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-blue-700">Link ID</label>
                          <input
                            type="text"
                            value={link.link_id}
                            onChange={(e) => handleLinkChange(idx, "link_id", e.target.value)}
                            placeholder="e.g. reports_to"
                            className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-blue-700">Display Name</label>
                          <input
                            type="text"
                            value={link.display_name}
                            onChange={(e) => handleLinkChange(idx, "display_name", e.target.value)}
                            placeholder="e.g. Reports To"
                            className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none"
                          />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-xs text-blue-700">Source Property</label>
                          <select
                            value={link.source_property_key}
                            onChange={(e) => handleLinkChange(idx, "source_property_key", e.target.value)}
                            className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                          >
                            <option value="">-- Select property --</option>
                            {properties
                              .filter((p) => p.included)
                              .map((p) => (
                                <option key={p.property_name} value={p.property_name}>
                                  {p.property_name} ({p.semantic_type})
                                </option>
                              ))}
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs text-blue-700">Target Object Type</label>
                          <select
                            value={link.target_object_type_id}
                            onChange={(e) => handleLinkChange(idx, "target_object_type_id", e.target.value)}
                            className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                          >
                            <option value="">-- Select object type --</option>
                            {(objectTypes || []).map((ot) => (
                              <option key={ot.id} value={ot.id}>
                                {ot.display_name} ({ot.object_type_key})
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                      <div>
                        <label className="block text-xs text-blue-700">Target Property Key</label>
                        <input
                          type="text"
                          value={link.target_property_key}
                          onChange={(e) => handleLinkChange(idx, "target_property_key", e.target.value)}
                          placeholder="e.g. id"
                          className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-blue-700">Cardinality</label>
                        <select
                          value={link.cardinality}
                          onChange={(e) => handleLinkChange(idx, "cardinality", e.target.value)}
                          className="mt-0.5 w-full rounded border border-blue-300 px-2 py-1 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                        >
                          <option value="many_to_one">many_to_one</option>
                          <option value="many_to_many">many_to_many</option>
                        </select>
                      </div>
                      {link.cardinality === "many_to_many" && (
                        <div className="rounded border border-amber-200 bg-amber-50 p-2">
                          <p className="text-xs text-amber-800">
                            many-to-many is metadata-only in v1. No executable join guarantees.
                          </p>
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Source Fields — read-only, expandable */}
      {data.nodeType === "source" && (
        <div className="p-4">
          <div className="mb-3 flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Type
            </span>
            <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600">
              {data.sourceType || "unknown"}
            </span>
          </div>

          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Fields ({(data.fields || []).length})
          </h4>
          {data.fields && data.fields.length > 0 ? (
            <ul className="space-y-1">
              {data.fields.map((field) => (
                <li
                  key={field}
                  className="rounded border border-zinc-100 bg-zinc-50 px-3 py-1.5 text-sm text-zinc-700"
                >
                  {field}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-zinc-500">No fields available</p>
          )}
        </div>
      )}

      {/* Dataset Node — read-only info */}
      {data.nodeType === "dataset" && (
        <div className="p-4">
          <p className="text-xs text-zinc-500">
            Dataset nodes are system-managed. Node labels and structure reflect
            system facts and cannot be edited directly.
          </p>
        </div>
      )}

      {/* Target Reference Node — read-only link info */}
      {isTarget && data.linkInfo && (
        <div className="p-4">
          <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Entity Link Reference
          </h4>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-zinc-500">Link ID</dt>
              <dd className="font-medium text-zinc-900">{data.linkInfo.link_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Source Key</dt>
              <dd className="text-zinc-700">{data.linkInfo.source_property_key}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Target Key</dt>
              <dd className="text-zinc-700">{data.linkInfo.target_property_key}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-zinc-500">Cardinality</dt>
              <dd>
                <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                  {data.linkInfo.cardinality}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
};
