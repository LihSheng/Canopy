"use client";

import { useEffect, useState } from "react";
import { fetchDatasets, fetchConnections } from "@/lib/api/data-source";
import { fetchDatasetVersionSchema } from "@/lib/api/semantic";
import type { SourceNode } from "@/lib/api/types";

type Props = {
  projectId: string;
  datasetId: string;
  sourceNodes: SourceNode[];
  onAdd: (nodes: SourceNode[]) => Promise<void>;
  onRemove: (sourceId: string) => void;
  onClose: () => void;
};

type KnownSource = {
  id: string;
  name: string;
  source_type: string;
  fields: string[];
};

export const SourceRegistrationDrawer = ({
  projectId,
  datasetId,
  sourceNodes,
  onAdd,
  onRemove,
  onClose,
}: Props) => {
  const [knownSources, setKnownSources] = useState<KnownSource[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingSources, setLoadingSources] = useState(true);
  const [addingSources, setAddingSources] = useState(false);

  // Load known sources: datasets + static_file connections
  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoadingSources(true);
      try {
        const [datasets, connections] = await Promise.all([
          fetchDatasets(projectId),
          fetchConnections(projectId),
        ]);

        if (cancelled) return;

        const sources: KnownSource[] = [];

        // Datasets as "dataset_table" sources
        for (const ds of datasets) {
          // Exclude the current dataset itself (circular self-reference)
          if (ds.id === datasetId) continue;
          sources.push({
            id: ds.id,
            name: ds.source_object_name || ds.name,
            source_type: "dataset_table",
            fields: [], // populated on selection
          });
        }

        // Static file connections
        for (const conn of connections) {
          if (conn.source_type === "static_file") {
            sources.push({
              id: conn.id,
              name: conn.name,
              source_type: "static_file",
              fields: [], // populated from schema if dataset exists for this connection
            });
          }
        }

        setKnownSources(sources);
      } catch {
        // Keep empty list
      } finally {
        if (!cancelled) setLoadingSources(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [projectId, datasetId]);

  // Filter to exclude already-registered sources
  const unregistered = knownSources.filter(
    (s) => !sourceNodes.some((sn) => sn.reference_id === s.id)
  );

  // Further filter by search query
  const visibleSources = searchQuery
    ? unregistered.filter((s) => s.name.toLowerCase().includes(searchQuery.toLowerCase()))
    : unregistered;

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const selectAllVisible = () => {
    setSelectedIds(new Set(visibleSources.map((s) => s.id)));
  };

  const deselectAll = () => {
    setSelectedIds(new Set());
  };

  const selectedCount = selectedIds.size;

  const handleAdd = async () => {
    if (selectedCount === 0) return;

    setAddingSources(true);
    try {
      // Fetch schemas for all selected sources in parallel
      const results = await Promise.allSettled(
        [...selectedIds].map(async (id) => {
          const source = knownSources.find((s) => s.id === id);
          if (!source) throw new Error(`Source ${id} not found`);

          let fields = source.fields;
          if (fields.length === 0 && source.source_type === "dataset_table") {
            const datasets = await fetchDatasets(projectId);
            const ds = datasets.find((d) => d.id === source.id);
            if (ds?.active_version_id) {
              const schema = await fetchDatasetVersionSchema(source.id, ds.active_version_id);
              fields = schema.map((col) => col.column_name);
            }
          }

          const node: SourceNode = {
            source_id: `src-${source.id}`,
            source_type: source.source_type,
            name: source.name,
            reference_id: source.id,
            fields,
          };
          return node;
        })
      );

      const nodes: SourceNode[] = [];
      const failed: string[] = [];
      for (const result of results) {
        if (result.status === "fulfilled") {
          nodes.push(result.value);
        } else {
          failed.push(result.reason instanceof Error ? result.reason.message : "Unknown error");
        }
      }

      if (nodes.length > 0) {
        await onAdd(nodes);
      }
      // If some failed, we report them — for now silently; toast can be added later
      void failed;

      setSelectedIds(new Set());
      onClose();
    } finally {
      setAddingSources(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-40 w-80 border-l border-zinc-200 bg-white shadow-lg overflow-y-auto">
      <div className="flex items-center justify-between border-b border-zinc-200 p-4">
        <h3 className="text-sm font-semibold text-zinc-900">Source Nodes</h3>
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

      {/* Existing source nodes */}
      <div className="p-4">
        {sourceNodes.length === 0 ? (
          <p className="text-xs text-zinc-500">No source nodes registered yet.</p>
        ) : (
          <ul className="space-y-2">
            {sourceNodes.map((sn) => (
              <li
                key={sn.source_id}
                className="flex items-center justify-between rounded border border-zinc-200 px-3 py-2 text-sm"
              >
                <div>
                  <span className="font-medium text-zinc-900">{sn.name}</span>
                  <span className="ml-2 text-xs text-zinc-400">({sn.source_type})</span>
                </div>
                <button
                  type="button"
                  onClick={() => onRemove(sn.source_id)}
                  title={`Remove ${sn.name}`}
                  className="shrink-0 rounded p-0.5 text-zinc-400 transition-colors hover:bg-rose-50 hover:text-rose-600"
                >
                  <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add new sources — checkbox list */}
      <div className="border-t border-zinc-200 p-4">
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Add Sources
        </h4>

        {loadingSources ? (
          <p className="text-xs text-zinc-400">Loading sources...</p>
        ) : unregistered.length === 0 ? (
          <p className="text-xs text-zinc-400">No additional sources available in this project.</p>
        ) : (
          <div className="space-y-2">
            {/* Search input */}
            <input
              type="text"
              placeholder="Search sources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none"
            />

            {/* Select All / Deselect All */}
            <div className="flex gap-3 text-xs">
              <button
                type="button"
                onClick={selectAllVisible}
                className="text-zinc-500 hover:text-zinc-800"
              >
                Select All
              </button>
              <button
                type="button"
                onClick={deselectAll}
                className="text-zinc-500 hover:text-zinc-800"
              >
                Deselect All
              </button>
            </div>

            {/* Checkbox list */}
            <ul className="max-h-64 space-y-1 overflow-y-auto">
              {visibleSources.map((src) => (
                <li key={src.id} className="flex items-center gap-2 rounded px-1 py-1 hover:bg-zinc-50">
                  <input
                    type="checkbox"
                    id={`src-${src.id}`}
                    checked={selectedIds.has(src.id)}
                    onChange={() => toggleSelection(src.id)}
                    className="size-3.5 rounded border-zinc-300 text-zinc-900 focus:ring-zinc-500"
                  />
                  <label htmlFor={`src-${src.id}`} className="flex flex-1 items-center gap-2 text-sm cursor-pointer">
                    <span className="font-medium text-zinc-900">{src.name}</span>
                    <span className="inline-block rounded-full border border-zinc-200 px-1.5 py-0.5 text-[10px] font-medium text-zinc-500">
                      {src.source_type}
                    </span>
                  </label>
                </li>
              ))}
            </ul>

            {/* Counter and Add button */}
            {selectedCount > 0 && (
              <p className="text-xs text-zinc-500">
                {selectedCount} selected
              </p>
            )}

            <button
              type="button"
              onClick={handleAdd}
              disabled={selectedCount === 0 || addingSources}
              className="w-full rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {addingSources
                ? "Loading schemas..."
                : `Add Source${selectedCount !== 1 ? "s" : ""}`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
