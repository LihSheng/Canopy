"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { evaluateFormula } from "@/lib/api/entities";

// ── Types ──────────────────────────────────────────────────────────────

export type EntityComputedProperty = {
  id: string;
  property_key: string;
  display_name: string;
  formula: string;
  formula_type: string;
  output_type: string;
  sort_order: number;
  is_active: boolean;
};

type Props = {
  existingPropertyKeys: string[];
  entityId: string;
  onAdd: (cp: EntityComputedProperty) => void;
  onCancel: () => void;
};

// ── Available functions ────────────────────────────────────────────────

const FUNCTIONS: { name: string; signature: string; description: string; category: string }[] = [
  { name: "upper", signature: "upper(text)", description: "Convert to uppercase", category: "Text" },
  { name: "lower", signature: "lower(text)", description: "Convert to lowercase", category: "Text" },
  { name: "trim", signature: "trim(text)", description: "Remove leading/trailing whitespace", category: "Text" },
  { name: "concat", signature: "concat(a, b, ...)", description: "Join values together", category: "Text" },
  { name: "length", signature: "length(text)", description: "Number of characters", category: "Text" },
  { name: "add", signature: "add(a, b)", description: "Add two numbers", category: "Math" },
  { name: "subtract", signature: "subtract(a, b)", description: "Subtract b from a", category: "Math" },
  { name: "multiply", signature: "multiply(a, b)", description: "Multiply two numbers", category: "Math" },
  { name: "divide", signature: "divide(a, b)", description: "Divide a by b", category: "Math" },
  { name: "coalesce", signature: "coalesce(a, b, ...)", description: "Return first non-null value", category: "Logic" },
  { name: "is_null", signature: "is_null(value)", description: "True if value is null", category: "Logic" },
  { name: "if", signature: "if(condition, then_val, else_val)", description: "Conditional value", category: "Logic" },
  { name: "equals", signature: "equals(a, b)", description: "True if a equals b", category: "Comparison" },
  { name: "greater_than", signature: "greater_than(a, b)", description: "True if a > b", category: "Comparison" },
  { name: "less_than", signature: "less_than(a, b)", description: "True if a < b", category: "Comparison" },
];

const SEMANTIC_TYPES = ["string", "number", "boolean", "datetime", "date"];

function generateId(): string {
  return `cp-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// ── Component ──────────────────────────────────────────────────────────

export const ComputedPropertyComposer = ({
  existingPropertyKeys,
  entityId,
  onAdd,
  onCancel,
}: Props) => {
  const [propertyKey, setPropertyKey] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [formula, setFormula] = useState("");
  const [outputType, setOutputType] = useState("string");
  const [formulaType, setFormulaType] = useState("arithmetic");
  const [sortOrder, setSortOrder] = useState(0);
  const [isActive, setIsActive] = useState(true);

  const [validationStatus, setValidationStatus] = useState<"idle" | "validating" | "valid" | "error">("idle");
  const [validationMessage, setValidationMessage] = useState("");
  const [previewResult, setPreviewResult] = useState<unknown>(null);
  const [showFunctionPalette, setShowFunctionPalette] = useState(false);
  const [autocompleteIdx, setAutocompleteIdx] = useState(-1);

  const formulaRef = useRef<HTMLTextAreaElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const existingKeysLower = new Set(existingPropertyKeys.map((k) => k.toLowerCase()));

  // ── Track cursor position (via event handlers, never during render) ──

  const [cursorPos, setCursorPos] = useState(formula.length);
  const captureCursor = useCallback(() => {
    if (formulaRef.current) {
      setCursorPos(formulaRef.current.selectionStart);
    }
  }, []);

  // ── Autocomplete suggestions ─────────────────────────────────────────

  const textBeforeCursor = formula.slice(0, cursorPos);
  const lastWordMatch = textBeforeCursor.match(/([a-z_][a-z0-9_]*)$/i);
  const partial = lastWordMatch ? lastWordMatch[1] : "";

  const suggestions =
    partial.length >= 1
      ? existingPropertyKeys.filter((k) => k.toLowerCase().startsWith(partial.toLowerCase()) && k.toLowerCase() !== partial.toLowerCase())
      : [];

  // ── Live validation (debounced) ──────────────────────────────────────

  const runValidation = useCallback(
    (f: string) => {
      if (!f.trim()) {
        setValidationStatus("idle");
        setValidationMessage("");
        setPreviewResult(null);
        return;
      }
      setValidationStatus("validating");
      evaluateFormula(entityId, f)
        .then((res) => {
          if (res.errors.length > 0) {
            setValidationStatus("error");
            setValidationMessage(res.errors[0]);
            setPreviewResult(null);
          } else {
            setValidationStatus("valid");
            setValidationMessage(res.warnings.length > 0 ? res.warnings[0] : "Formula is valid");
            setPreviewResult(res.result);
          }
        })
        .catch(() => {
          setValidationStatus("error");
          setValidationMessage("Validation request failed");
          setPreviewResult(null);
        });
    },
    [entityId]
  );

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runValidation(formula), 400);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [formula, runValidation]);

  // ── Keyboard handlers ────────────────────────────────────────────────

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Tab: accept top autocomplete suggestion
    if (e.key === "Tab" && suggestions.length > 0) {
      e.preventDefault();
      const match = lastWordMatch;
      if (match) {
        const suggestion = autocompleteIdx >= 0 ? suggestions[autocompleteIdx] : suggestions[0];
        const start = match.index!;
        const newFormula = formula.slice(0, start) + suggestion + formula.slice(cursorPos);
        setFormula(newFormula);
        setAutocompleteIdx(-1);
      }
      return;
    }
    // Arrow keys: navigate suggestions
    if (e.key === "ArrowDown" && suggestions.length > 0) {
      e.preventDefault();
      setAutocompleteIdx((prev) => Math.min(prev + 1, suggestions.length - 1));
      return;
    }
    if (e.key === "ArrowUp" && suggestions.length > 0) {
      e.preventDefault();
      setAutocompleteIdx((prev) => Math.max(prev - 1, -1));
      return;
    }
    // Escape: close autocomplete
    if (e.key === "Escape") {
      setAutocompleteIdx(-1);
      return;
    }
    setAutocompleteIdx(-1);
  };

  // ── Insert function template ─────────────────────────────────────────

  const insertFunction = (fnName: string) => {
    const textarea = formulaRef.current;
    if (!textarea) {
      setFormula((prev) => prev + `${fnName}()`);
      return;
    }
    const pos = textarea.selectionStart;
    const before = formula.slice(0, pos);
    const after = formula.slice(pos);
    setFormula(`${before}${fnName}()${after}`);
    // Focus back and place cursor inside the parentheses
    setTimeout(() => {
      textarea.focus();
      textarea.selectionStart = pos + fnName.length + 1;
      textarea.selectionEnd = pos + fnName.length + 1;
    }, 0);
  };

  // ── Submit ───────────────────────────────────────────────────────────

  const handleSubmit = () => {
    const trimmedKey = propertyKey.trim();
    if (!trimmedKey) {
      setValidationStatus("error");
      setValidationMessage("Property key is required.");
      return;
    }
    if (!/^[a-z][a-z0-9_]*$/.test(trimmedKey)) {
      setValidationStatus("error");
      setValidationMessage("Property key must be snake_case (lowercase letters, digits, underscores).");
      return;
    }
    if (existingKeysLower.has(trimmedKey.toLowerCase())) {
      setValidationStatus("error");
      setValidationMessage(`Property key "${trimmedKey}" already exists.`);
      return;
    }
    if (!formula.trim()) {
      setValidationStatus("error");
      setValidationMessage("Formula is required.");
      return;
    }
    if (validationStatus === "error") {
      setValidationStatus("error");
      setValidationMessage("Fix formula errors before adding.");
      return;
    }

    const cp: EntityComputedProperty = {
      id: generateId(),
      property_key: trimmedKey,
      display_name: displayName.trim() || trimmedKey,
      formula: formula.trim(),
      formula_type: formulaType,
      output_type: outputType,
      sort_order: sortOrder,
      is_active: isActive,
    };
    onAdd(cp);
  };

  // ── Render ───────────────────────────────────────────────────────────

  const groupedFunctions: Record<string, typeof FUNCTIONS> = {};
  for (const fn of FUNCTIONS) {
    (groupedFunctions[fn.category] ??= []).push(fn);
  }

  return (
    <div className="rounded border border-purple-200 bg-purple-50 p-4">
      <h5 className="mb-3 text-xs font-semibold text-purple-800">
        Compose Computed Property
      </h5>

      {validationMessage && validationStatus === "error" && (
        <div className="mb-3 rounded border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {validationMessage}
        </div>
      )}

      <div className="space-y-3">
        {/* Property Key */}
        <div>
          <label className="block text-xs text-purple-700">Property Key</label>
          <input
            type="text"
            value={propertyKey}
            onChange={(e) => setPropertyKey(e.target.value)}
            placeholder="e.g. total_comp"
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Display Name */}
        <div>
          <label className="block text-xs text-purple-700">Display Name</label>
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="e.g. Total Compensation"
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 placeholder-zinc-400 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Output Type */}
        <div>
          <label className="block text-xs text-purple-700">Output Type</label>
          <select
            value={outputType}
            onChange={(e) => setOutputType(e.target.value)}
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
          >
            {SEMANTIC_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        {/* Formula */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-xs text-purple-700">Formula</label>
            <button
              type="button"
              onClick={() => setShowFunctionPalette((s) => !s)}
              className="text-xs text-purple-500 hover:text-purple-700 underline"
            >
              {showFunctionPalette ? "Hide functions" : "Show functions"}
            </button>
          </div>

          {/* Function palette */}
          {showFunctionPalette && (
            <div className="mb-2 rounded border border-purple-200 bg-white p-2 max-h-40 overflow-y-auto">
              {Object.entries(groupedFunctions).map(([category, fns]) => (
                <div key={category} className="mb-1 last:mb-0">
                  <span className="text-[10px] font-semibold text-purple-400 uppercase tracking-wide">{category}</span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {fns.map((fn) => (
                      <button
                        key={fn.name}
                        type="button"
                        onClick={() => insertFunction(fn.name)}
                        title={fn.description}
                        className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-mono text-purple-700 hover:bg-purple-200 transition-colors"
                      >
                        {fn.signature}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Formula textarea with autocomplete */}
          <div className="relative">
            <textarea
              ref={formulaRef}
              value={formula}
              onChange={(e) => {
                setFormula(e.target.value);
                setCursorPos(e.target.selectionStart);
              }}
              onKeyUp={captureCursor}
              onMouseUp={captureCursor}
              onKeyDown={handleKeyDown}
              placeholder={'e.g. concat(upper(first_name), " ", upper(last_name))'}
              rows={3}
              className="w-full rounded border border-purple-300 px-2 py-1.5 text-xs font-mono text-zinc-900 placeholder-zinc-400 focus:border-purple-500 focus:outline-none resize-y"
            />

            {/* Autocomplete dropdown */}
            {suggestions.length > 0 && (
              <div className="absolute left-0 top-full z-10 mt-0.5 w-full rounded border border-purple-200 bg-white shadow-sm">
                {suggestions.map((s, i) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => {
                      const match = lastWordMatch;
                      if (match) {
                        const start = match.index!;
                        const newFormula = formula.slice(0, start) + s + formula.slice(cursorPos);
                        setFormula(newFormula);
                      }
                      formulaRef.current?.focus();
                    }}
                    className={`block w-full px-2 py-1 text-left text-xs text-zinc-700 hover:bg-purple-50 ${i === autocompleteIdx ? "bg-purple-100" : ""}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Validation indicator */}
          <div className="mt-1 flex items-center gap-1.5">
            {validationStatus === "validating" && (
              <span className="text-[10px] text-purple-400">Validating...</span>
            )}
            {validationStatus === "valid" && (
              <span className="text-[10px] text-emerald-600">{validationMessage}</span>
            )}
            {validationStatus === "error" && validationMessage && (
              <span className="text-[10px] text-rose-600">{validationMessage}</span>
            )}
          </div>

          {/* Preview */}
          {previewResult !== null && (
            <div className="mt-1 rounded border border-emerald-200 bg-emerald-50 px-2 py-1">
              <span className="text-[10px] text-emerald-600 font-medium">Preview:</span>{" "}
              <span className="text-xs text-emerald-800 font-mono">
                {typeof previewResult === "string" ? `"${previewResult}"` : String(previewResult)}
              </span>
            </div>
          )}
        </div>

        {/* Formula Type */}
        <div>
          <label className="block text-xs text-purple-700">Formula Type</label>
          <select
            value={formulaType}
            onChange={(e) => setFormulaType(e.target.value)}
            className="mt-1 w-full rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
          >
            <option value="arithmetic">Arithmetic</option>
            <option value="text">Text</option>
            <option value="logical">Logical</option>
            <option value="lookup">Lookup / Coalesce</option>
          </select>
        </div>

        {/* Sort Order */}
        <div>
          <label className="block text-xs text-purple-700">Sort Order</label>
          <input
            type="number"
            value={sortOrder}
            onChange={(e) => setSortOrder(parseInt(e.target.value) || 0)}
            min={0}
            className="mt-1 w-24 rounded border border-purple-300 px-2 py-1.5 text-xs text-zinc-900 focus:border-purple-500 focus:outline-none"
          />
        </div>

        {/* Active toggle */}
        <div>
          <label className="flex items-center gap-1.5 text-xs text-purple-700">
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="rounded border-purple-300"
            />
            Active
          </label>
        </div>

        {/* Properties reference list */}
        <div>
          <label className="block text-xs text-purple-700 mb-1">
            Available Properties
          </label>
          <div className="flex flex-wrap gap-1">
            {existingPropertyKeys.length === 0 ? (
              <span className="text-xs text-purple-400">No base properties defined yet.</span>
            ) : (
              existingPropertyKeys.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => insertFunction(key)}
                  className="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-mono text-purple-700 hover:bg-purple-200 transition-colors"
                  title={`Insert property "${key}" into formula`}
                >
                  {key}
                </button>
              ))
            )}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!propertyKey.trim() || !formula.trim()}
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
