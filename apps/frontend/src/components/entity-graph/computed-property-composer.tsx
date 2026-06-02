"use client";

import { useState } from "react";

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

type SourceNodeData = {
  source_id: string;
  name: string;
  fields: string[];
};

type Props = {
  sourceNodes: SourceNodeData[];
  existingProps: { name: string }[]; // for duplicate name checking
  onAdd: (cp: ComputedProperty) => void;
  onCancel: () => void;
};

const COMPOSITION_KINDS = [
  { value: "concat", label: "Concatenation" },
  { value: "template", label: "Template" },
  { value: "lookup", label: "Lookup" },
];

const SEMANTIC_TYPES = ["string", "integer", "number", "boolean", "datetime", "date"];

function generateId(): string {
  return `cp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export const ComputedPropertyComposer = ({
  sourceNodes,
  existingProps,
  onAdd,
  onCancel,
}: Props) => {
  const [propertyName, setPropertyName] = useState("");
  const [semanticType, setSemanticType] = useState("string");
  const [compositionKind, setCompositionKind] = useState("concat");
  const [expression, setExpression] = useState("");
  const [included, setIncluded] = useState(true);
  const [inputs, setInputs] = useState<FieldRef[]>([]);
  const [addErr, setAddErr] = useState<string | null>(null);

  // Track current field picker state
  const [pickSourceId, setPickSourceId] = useState("");
  const [pickFieldName, setPickFieldName] = useState("");

  const allPropNames = new Set(existingProps.map((p) => p.name.toLowerCase()));

  const handleAddInput = () => {
    const sid = pickSourceId.trim();
    const fname = pickFieldName.trim();
    if (!fname) return;

    const source = sourceNodes.find((sn) => sn.source_id === sid || (!sid && sn.fields.includes(fname)));
    const resolvedSourceId = source?.source_id || sid;
    const resolvedSourceName = source?.name || "";

    // Check duplicate input
    const dup = inputs.find(
      (inp) =>
        inp.source_id === resolvedSourceId && inp.field_name === fname
    );
    if (dup) {
      setAddErr("This field reference is already added.");
      return;
    }

    setInputs((prev) => [
      ...prev,
      {
        source_id: resolvedSourceId,
        source_name: resolvedSourceName,
        field_name: fname,
      },
    ]);
    setPickSourceId("");
    setPickFieldName("");
    setAddErr(null);
  };

  const handleRemoveInput = (idx: number) => {
    setInputs((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = () => {
    const trimmedName = propertyName.trim();
    if (!trimmedName) {
      setAddErr("Property name is required.");
      return;
    }
    if (allPropNames.has(trimmedName.toLowerCase())) {
      setAddErr(`Property name "${trimmedName}" already exists.`);
      return;
    }
    if (inputs.length === 0) {
      setAddErr("At least one input field reference is required.");
      return;
    }

    const cp: ComputedProperty = {
      id: generateId(),
      property_name: trimmedName,
      semantic_type: semanticType,
      composition_kind: compositionKind,
      expression: expression.trim(),
      inputs,
      included,
    };

    onAdd(cp);
  };

  // Get available fields for the selected source
  const selectedSourceFields = pickSourceId
    ? sourceNodes.find((sn) => sn.source_id === pickSourceId)?.fields || []
    : [];

  return (
    <div className="rounded border border-purple-200 bg-purple-50 p-4">
      <h5 className="mb-3 text-xs font-semibold text-purple-800">
        Compose Computed Property
      </h5>

      {addErr && (
        <div className="mb-3 rounded border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {addErr}
        </div>
      )}

      <div className="space-y-3">
        {/* Property Name */}
        <div>
          <label className="block text-xs text-purple-700">Property Name</label>
          <input
            type="text"
            value={propertyName}
            onChange={(e) => setPropertyName(e.target.value)}
            placeholder="e.g. full_name"
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Composition Kind */}
        <div>
          <label className="block text-xs text-purple-700">Composition Kind</label>
          <select
            value={compositionKind}
            onChange={(e) => setCompositionKind(e.target.value)}
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
          >
            {COMPOSITION_KINDS.map((k) => (
              <option key={k.value} value={k.value}>{k.label}</option>
            ))}
          </select>
        </div>

        {/* Semantic Type */}
        <div>
          <label className="block text-xs text-purple-700">Semantic Type</label>
          <select
            value={semanticType}
            onChange={(e) => setSemanticType(e.target.value)}
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
          >
            {SEMANTIC_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Expression */}
        <div>
          <label className="block text-xs text-purple-700">
            Expression / Template
            <span className="text-purple-400 ml-1">(optional)</span>
          </label>
          <input
            type="text"
            value={expression}
            onChange={(e) => setExpression(e.target.value)}
            placeholder={
              compositionKind === "concat"
                ? 'e.g. "{first} {last}"'
                : 'e.g. "lookup.reference_table"'
            }
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Input Field References */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-xs text-purple-700">
              Input Fields ({inputs.length})
            </label>
          </div>

          {/* Add input picker */}
          <div className="mb-2 space-y-1.5">
            {sourceNodes.length === 0 ? (
              <p className="text-xs text-purple-400">
                No source nodes connected. Add source nodes first.
              </p>
            ) : (
              <>
                {/* Source node picker */}
                <div className="flex gap-1.5">
                  <select
                    value={pickSourceId}
                    onChange={(e) => {
                      setPickSourceId(e.target.value);
                      setPickFieldName("");
                    }}
                    className="flex-1 rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
                  >
                    <option value="">-- Any source --</option>
                    {sourceNodes.map((sn) => (
                      <option key={sn.source_id} value={sn.source_id}>
                        {sn.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Field picker */}
                {pickSourceId ? (
                  <div className="flex gap-1.5">
                    <select
                      value={pickFieldName}
                      onChange={(e) => setPickFieldName(e.target.value)}
                      className="flex-1 rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
                    >
                      <option value="">-- Select field --</option>
                      {selectedSourceFields.map((f) => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleAddInput}
                      disabled={!pickFieldName}
                      className="rounded bg-purple-600 px-2 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      + Add
                    </button>
                  </div>
                ) : (
                  /* Field picker across all sources when no source selected */
                  <div className="flex gap-1.5">
                    <select
                      value={pickFieldName}
                      onChange={(e) => setPickFieldName(e.target.value)}
                      className="flex-1 rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
                    >
                      <option value="">-- Select field --</option>
                      {sourceNodes.flatMap((sn) =>
                        (sn.fields || []).map((f) => (
                          <option key={`${sn.source_id}:${f}`} value={f}>
                            {sn.name}.{f}
                          </option>
                        ))
                      )}
                    </select>
                    <button
                      type="button"
                      onClick={handleAddInput}
                      disabled={!pickFieldName}
                      className="rounded bg-purple-600 px-2 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      + Add
                    </button>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Input list preview */}
          {inputs.length > 0 && (
            <ul className="space-y-1">
              {inputs.map((inp, idx) => (
                <li
                  key={idx}
                  className="flex items-center justify-between rounded border border-purple-200 bg-white px-2 py-1"
                >
                  <span className="text-xs text-zinc-700">
                    {inp.source_name && (
                      <span className="text-purple-500 font-medium">{inp.source_name}.</span>
                    )}
                    {inp.field_name}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveInput(idx)}
                    className="rounded px-1 py-0.5 text-xs text-rose-400 hover:text-rose-600 hover:bg-rose-50"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Include toggle */}
        <div>
          <label className="flex items-center gap-1.5 text-xs text-purple-700">
            <input
              type="checkbox"
              checked={included}
              onChange={(e) => setIncluded(e.target.checked)}
              className="rounded border-purple-300"
            />
            Include property in mapping
          </label>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!propertyName.trim() || inputs.length === 0}
            className="flex-1 rounded bg-purple-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Add Computed Property
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded border border-purple-200 bg-white px-3 py-1.5 text-xs font-medium text-purple-700 transition-colors hover:bg-purple-50"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
