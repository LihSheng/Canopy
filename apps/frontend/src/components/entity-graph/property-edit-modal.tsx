"use client";

import { useState, type MouseEvent, useEffect, useId } from "react";
import type { EntityRevisionProperty, SourceBinding } from "@/lib/api/types";

// ─── Types ────────────────────────────────────────────────────────────────

export type SourceNodeInfo = {
  source_id: string;
  name: string;
  source_type: string;
  fields: string[];
};

export type PropertyFieldValues = {
  property_key: string;
  display_name: string;
  semantic_type: string;
  is_required: boolean;
  is_primary_key: boolean;
};

export type PropertySaveData = {
  propertyFields: PropertyFieldValues;
  binding: SourceBinding | null;
};

/** Internal binding state — property_key is dynamic (key may change in create mode). */
type RawBinding = {
  source_node_id: string;
  source_field_name: string;
};

type Props = {
  open: boolean;
  /** null = create mode; non-null = edit mode */
  property: EntityRevisionProperty | null;
  /** The current binding for this property (null if unbound) */
  existingBinding: SourceBinding | null;
  /** Available source nodes with their field lists */
  sourceNodes: SourceNodeInfo[];
  /** Called on save */
  onSave: (data: PropertySaveData) => Promise<void>;
  /** Called on remove (edit mode only) */
  onRemove?: () => Promise<void>;
  onClose: () => void;
  loading?: boolean;
};

// ─── Constants ────────────────────────────────────────────────────────────

const SEMANTIC_TYPES = ["string", "integer", "number", "boolean", "datetime", "date"] as const;

const semanticTypeLabel = (t: string): string => {
  const labels: Record<string, string> = {
    string: "String",
    integer: "Integer",
    number: "Number",
    boolean: "Boolean",
    datetime: "DateTime",
    date: "Date",
  };
  return labels[t] || t;
};

// ─── Component ────────────────────────────────────────────────────────────

export const PropertyEditModal = ({
  open,
  property,
  existingBinding,
  sourceNodes,
  onSave,
  onRemove,
  onClose,
  loading = false,
}: Props) => {
  const isCreate = !property;
  const titleId = useId();

  // ── Form state ────────────────────────────────────────────────────────

  const [displayName, setDisplayName] = useState("");
  const [propertyKey, setPropertyKey] = useState("");
  const [semanticType, setSemanticType] = useState("string");
  const [isRequired, setIsRequired] = useState(false);
  const [isPrimaryKey, setIsPrimaryKey] = useState(false);
  const [binding, setBinding] = useState<RawBinding | null>(null);

  const [saving, setSaving] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ── Init / reset when modal opens ──────────────────────────────────────

  useEffect(() => {
    if (!open) return;

    if (property) {
      setDisplayName(property.display_name);
      setPropertyKey(property.property_key);
      setSemanticType(property.semantic_type);
      setIsRequired(property.is_required);
      setIsPrimaryKey(property.is_primary_key);
      setBinding(
        existingBinding
          ? {
              source_node_id: existingBinding.source_node_id,
              source_field_name: existingBinding.source_field_name,
            }
          : null
      );
    } else {
      setDisplayName("");
      setPropertyKey("");
      setSemanticType("string");
      setIsRequired(false);
      setIsPrimaryKey(false);
      setBinding(null);
    }

    setError(null);
    setSaving(false);
    setRemoving(false);
  }, [open, property, existingBinding]);

  // ── Keyboard / scroll lock ─────────────────────────────────────────────

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !saving && !removing) onClose();
    };
    window.addEventListener("keydown", onKeyDown);

    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = prev;
    };
  }, [open, saving, removing, onClose]);

  // ── Handlers ───────────────────────────────────────────────────────────

  const handleBackdrop = (e: MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget && !saving && !removing) onClose();
  };

  const handleBind = (sourceNodeId: string, fieldName: string) => {
    setBinding({
      source_node_id: sourceNodeId,
      source_field_name: fieldName,
    });
  };

  const handleUnbind = () => setBinding(null);

  const handleSave = async () => {
    if (!displayName.trim() || !propertyKey.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const currentKey = propertyKey.trim();
      const fullBinding: SourceBinding | null = binding
        ? {
            property_key: currentKey,
            source_node_id: binding.source_node_id,
            source_field_name: binding.source_field_name,
          }
        : null;

      await onSave({
        propertyFields: {
          property_key: currentKey,
          display_name: displayName.trim(),
          semantic_type: semanticType,
          is_required: isRequired,
          is_primary_key: isPrimaryKey,
        },
        binding: fullBinding,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save property");
    } finally {
      setSaving(false);
    }
  };

  const handleRemove = async () => {
    if (!onRemove) return;
    setRemoving(true);
    setError(null);
    try {
      await onRemove();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove property");
    } finally {
      setRemoving(false);
    }
  };

  const busy = saving || removing || loading;
  const canSave = displayName.trim().length > 0 && propertyKey.trim().length > 0;

  if (!open) return null;

  // ── Render ─────────────────────────────────────────────────────────────

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto px-4 py-10 sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      onClick={handleBackdrop}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-zinc-950/40 backdrop-blur-[1px]" aria-hidden />

      {/* Card */}
      <div className="relative w-full max-w-lg rounded-2xl border border-zinc-200 bg-white shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-zinc-100 px-6 py-4">
          <h2 id={titleId} className="text-base font-semibold text-zinc-900">
            {isCreate ? "Add Property" : "Edit Property"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="rounded p-1 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-600 disabled:opacity-50"
            aria-label="Close"
          >
            <svg className="size-4" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
              <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="space-y-4 px-6 py-4">
          {error && (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-600">
              {error}
            </div>
          )}

          {/* Display Name */}
          <div>
            <label
              htmlFor={`${titleId}-display-name`}
              className="mb-1 block text-xs font-medium text-zinc-700"
            >
              Display Name
            </label>
            <input
              id={`${titleId}-display-name`}
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="e.g. Employee Name"
              disabled={busy}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Property Key */}
          <div>
            <label
              htmlFor={`${titleId}-property-key`}
              className="mb-1 block text-xs font-medium text-zinc-700"
            >
              Key
            </label>
            <input
              id={`${titleId}-property-key`}
              type="text"
              value={propertyKey}
              onChange={(e) =>
                setPropertyKey(
                  e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_")
                )
              }
              placeholder="snake_case_key"
              disabled={busy}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 font-mono text-sm text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
            />
          </div>

          {/* Semantic Type */}
          <div>
            <label
              htmlFor={`${titleId}-semantic-type`}
              className="mb-1 block text-xs font-medium text-zinc-700"
            >
              Type
            </label>
            <select
              id={`${titleId}-semantic-type`}
              value={semanticType}
              onChange={(e) => setSemanticType(e.target.value)}
              disabled={busy}
              className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
            >
              {SEMANTIC_TYPES.map((t) => (
                <option key={t} value={t}>
                  {semanticTypeLabel(t)}
                </option>
              ))}
            </select>
          </div>

          {/* Checkboxes */}
          <div className="flex items-center gap-6">
            <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-700">
              <input
                type="checkbox"
                checked={isRequired}
                onChange={(e) => setIsRequired(e.target.checked)}
                disabled={busy}
                className="rounded border-zinc-300 text-blue-600 focus:ring-blue-500"
              />
              Required
            </label>
            <label className="flex cursor-pointer items-center gap-2 text-sm text-zinc-700">
              <input
                type="checkbox"
                checked={isPrimaryKey}
                onChange={(e) => setIsPrimaryKey(e.target.checked)}
                disabled={busy}
                className="rounded border-zinc-300 text-blue-600 focus:ring-blue-500"
              />
              Primary Key
            </label>
          </div>

          {/* Source Binding */}
          <div>
            <label className="mb-2 block text-xs font-medium text-zinc-700">
              Source Binding
            </label>
            {sourceNodes.length === 0 ? (
              <p className="text-xs italic text-zinc-400">
                No source nodes available. Add source nodes to bind fields.
              </p>
            ) : binding ? (
              /* Bound state */
              <div className="flex items-center gap-2 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2">
                <span className="flex-1 font-mono text-xs text-emerald-800">
                  {(sourceNodes.find((sn) => sn.source_id === binding.source_node_id)
                    ?.name || binding.source_node_id)}
                  .{binding.source_field_name}
                </span>
                <button
                  type="button"
                  onClick={handleUnbind}
                  disabled={busy}
                  className="rounded px-1.5 py-0.5 text-xs text-rose-500 hover:bg-rose-100 disabled:opacity-50"
                >
                  Unbind
                </button>
              </div>
            ) : (
              /* Unbound state — show one dropdown per source node */
              <div className="space-y-2">
                {sourceNodes.map((sn) => (
                  <select
                    key={sn.source_id}
                    value=""
                    disabled={busy}
                    onChange={(e) => {
                      if (e.target.value) handleBind(sn.source_id, e.target.value);
                    }}
                    className="w-full rounded-md border border-zinc-200 px-3 py-2 text-sm text-zinc-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                  >
                    <option value="">{sn.name} — select field</option>
                    {sn.fields.map((field) => (
                      <option key={field} value={field}>
                        {field}
                      </option>
                    ))}
                  </select>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-zinc-100 px-6 py-4">
          <div>
            {!isCreate && onRemove && (
              <button
                type="button"
                onClick={handleRemove}
                disabled={busy}
                className="rounded-md px-3 py-1.5 text-xs font-medium text-rose-600 hover:bg-rose-50 disabled:opacity-50"
              >
                {removing ? "Removing..." : "Remove Property"}
              </button>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={busy}
              className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 hover:bg-zinc-50 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={busy || !canSave}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
