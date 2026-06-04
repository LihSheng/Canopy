"use client";

import { useState } from "react";
import type { EntityRevisionProperty, SourceBinding } from "@/lib/api/types";

type SourceNodeInfo = {
  source_id: string;
  name: string;
  source_type: string;
  fields: string[];
};

type Props = {
  properties: EntityRevisionProperty[];
  bindings: SourceBinding[];
  sourceNodes: SourceNodeInfo[];
  onSetBindings: (bindings: SourceBinding[]) => Promise<void>;
  disabled?: boolean;
};

export const SourceBindingEditor = ({
  properties,
  bindings,
  sourceNodes,
  onSetBindings,
  disabled,
}: Props) => {
  const [editing, setEditing] = useState(false);
  const [localBindings, setLocalBindings] = useState<SourceBinding[]>(bindings);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Build lookup maps
  const bindingByPropKey = new Map<string, SourceBinding>();
  localBindings.forEach((b) => bindingByPropKey.set(b.property_key, b));

  const getSourceNodeName = (sourceId: string): string => {
    const sn = sourceNodes.find((s) => s.source_id === sourceId);
    return sn?.name || sourceId;
  };

  // Detect broken bindings
  const propertyKeys = new Set(properties.map((p) => p.property_key));
  const sourceNodeIds = new Set(sourceNodes.map((s) => s.source_id));
  const brokenBindings = localBindings.filter(
    (b) =>
      !propertyKeys.has(b.property_key) ||
      !sourceNodeIds.has(b.source_node_id)
  );

  const handleBind = (
    propertyKey: string,
    sourceNodeId: string,
    sourceFieldName: string
  ) => {
    const updated = localBindings.filter((b) => b.property_key !== propertyKey);
    updated.push({ property_key: propertyKey, source_node_id: sourceNodeId, source_field_name: sourceFieldName });
    setLocalBindings(updated);
  };

  const handleUnbind = (propertyKey: string) => {
    setLocalBindings(localBindings.filter((b) => b.property_key !== propertyKey));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await onSetBindings(localBindings);
      setEditing(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save bindings");
    } finally {
      setSaving(false);
    }
  };

  const handleStartEdit = () => {
    setLocalBindings([...bindings]);
    setError(null);
    setEditing(true);
  };

  const handleCancel = () => {
    setLocalBindings(bindings);
    setEditing(false);
    setError(null);
  };

  // Unbound required properties
  const unboundRequired = properties.filter(
    (p) =>
      p.is_required && !bindingByPropKey.has(p.property_key)
  );

  // Get source field options for a source node
  const getSourceFields = (sourceNodeId: string): string[] => {
    const sn = sourceNodes.find((s) => s.source_id === sourceNodeId);
    return sn?.fields || [];
  };

  if (!editing) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white">
        <div className="flex items-center justify-between border-b border-zinc-100 px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold text-zinc-900">
              Source Bindings
              <span className="ml-1.5 text-xs font-normal text-zinc-400">
                ({bindings.length})
              </span>
            </h3>
          </div>
          {!disabled && (
            <button
              type="button"
              onClick={handleStartEdit}
              className="text-xs font-medium text-zinc-600 hover:text-zinc-900"
            >
              Edit Bindings
            </button>
          )}
        </div>

        {/* Broken bindings warning */}
        {brokenBindings.length > 0 && (
          <div className="border-b border-amber-200 bg-amber-50 px-4 py-2">
            <p className="text-xs font-medium text-amber-800">
              {brokenBindings.length} broken binding{brokenBindings.length !== 1 ? "s" : ""} detected
            </p>
            {brokenBindings.map((b, i) => (
              <p key={i} className="mt-0.5 text-xs text-amber-700">
                {!propertyKeys.has(b.property_key)
                  ? `Missing property: "${b.property_key}"`
                  : `Missing source node: "${b.source_node_id}"`}
              </p>
            ))}
          </div>
        )}

        {/* Unbound required properties warning */}
        {unboundRequired.length > 0 && (
          <div className="border-b border-red-200 bg-red-50 px-4 py-2">
            <p className="text-xs font-medium text-red-700">
              {unboundRequired.length} required propert{unboundRequired.length !== 1 ? "ies" : "y"} unbound
            </p>
            {unboundRequired.map((p) => (
              <p key={p.property_id} className="mt-0.5 text-xs text-red-600">
                &quot;{p.display_name}&quot; ({p.property_key}) requires a source binding
              </p>
            ))}
          </div>
        )}

        {bindings.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-zinc-400">
            No source bindings configured yet. Click &quot;Edit Bindings&quot; to map source fields to properties.
          </div>
        ) : (
          <table className="min-w-full divide-y divide-zinc-100 text-sm">
            <thead>
              <tr className="bg-zinc-50">
                <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Property
                </th>
                <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Source Field
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100">
              {bindings.map((b) => (
                <tr key={`${b.property_key}-${b.source_node_id}-${b.source_field_name}`} className="hover:bg-zinc-50">
                  <td className="px-4 py-2 font-mono text-xs text-zinc-900">
                    {b.property_key}
                  </td>
                  <td className="px-4 py-2 text-xs text-zinc-500">
                    <span className="inline-block rounded bg-emerald-50 px-2 py-0.5 font-mono text-emerald-700">
                      {getSourceNodeName(b.source_node_id)}.{b.source_field_name}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  // Editing mode
  return (
    <div className="rounded-lg border border-blue-200 bg-white">
      <div className="flex items-center justify-between border-b border-blue-200 px-4 py-3">
        <h3 className="text-sm font-semibold text-zinc-900">Edit Source Bindings</h3>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCancel}
            className="text-xs font-medium text-zinc-500 hover:text-zinc-900"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-4 py-2 text-xs text-red-600">
          {error}
        </div>
      )}

      {sourceNodes.length === 0 ? (
        <div className="px-4 py-6 text-center text-sm text-zinc-400">
          No source nodes available. Add source nodes in the graph editor first.
        </div>
      ) : (
        <table className="min-w-full divide-y divide-zinc-100 text-sm">
          <thead>
            <tr className="bg-zinc-50">
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Property
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Required
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Bound To
              </th>
              <th className="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {properties.map((prop) => {
              const binding = bindingByPropKey.get(prop.property_key);
              return (
                <tr key={prop.property_id} className="hover:bg-zinc-50">
                  <td className="px-4 py-2">
                    <span className="font-medium text-zinc-900">{prop.display_name}</span>
                    <span className="ml-2 font-mono text-xs text-zinc-400">
                      {prop.property_key}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {prop.is_required ? (
                      <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                        Req
                      </span>
                    ) : (
                      <span className="text-zinc-300">{'\u2014'}</span>
                    )}
                  </td>
                  <td className="px-4 py-2">
                    {binding ? (
                      <span className="inline-block rounded bg-emerald-50 px-2 py-0.5 font-mono text-xs text-emerald-700">
                        {getSourceNodeName(binding.source_node_id)}.{binding.source_field_name}
                      </span>
                    ) : (
                      <span className="text-xs text-zinc-400 italic">Unbound</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">
                    <div className="flex items-center justify-end gap-1">
                      {sourceNodes.map((sn) => (
                        <select
                          key={sn.source_id}
                          value={binding && binding.source_node_id === sn.source_id ? binding.source_field_name : ""}
                          onChange={(e) => {
                            if (e.target.value) {
                              handleBind(prop.property_key, sn.source_id, e.target.value);
                            }
                          }}
                          className="rounded border border-zinc-200 px-1.5 py-0.5 text-xs text-zinc-900 focus:border-blue-500 focus:outline-none"
                          title={`Bind from ${sn.name}`}
                        >
                          <option value="">{sn.name}: --</option>
                          {getSourceFields(sn.source_id).map((field) => (
                            <option key={field} value={field}>
                              {field}
                            </option>
                          ))}
                        </select>
                      ))}
                      {binding && (
                        <button
                          type="button"
                          onClick={() => handleUnbind(prop.property_key)}
                          className="rounded px-1 py-0.5 text-xs text-rose-400 hover:bg-rose-50 hover:text-rose-600"
                          title="Remove binding"
                        >
                          x
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};
