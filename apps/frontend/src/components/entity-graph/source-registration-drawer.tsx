"use client";

import { useEffect, useState } from "react";
import { fetchDatasets, fetchConnections } from "@/lib/api/data-source";
import { fetchDatasetVersionSchema } from "@/lib/api/semantic";
import type { SourceNode } from "@/lib/api/types";

type Props = {
  projectId: string;
  datasetId: string;
  sourceNodes: SourceNode[];
  onAdd: (node: SourceNode) => void;
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
  const [sourceType, setSourceType] = useState<"dataset_table" | "static_file">("dataset_table");
  const [knownSources, setKnownSources] = useState<KnownSource[]>([]);
  const [selectedSourceId, setSelectedSourceId] = useState("");
  const [loadingSources, setLoadingSources] = useState(true);
  const [fetchingSchema, setFetchingSchema] = useState(false);

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
          // Exclude the current dataset itself
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

  // Filter sources by selected type
  const filteredSources = knownSources.filter((s) => s.source_type === sourceType);
  const selectedSource = knownSources.find((s) => s.id === selectedSourceId);
  const alreadyRegistered = sourceNodes.map((sn) => sn.reference_id);

  const handleAdd = async () => {
    if (!selectedSourceId || !selectedSource) return;

    // Fetch schema fields for the source if not already loaded
    let fields = selectedSource.fields;
    if (fields.length === 0) {
      setFetchingSchema(true);
      try {
        if (selectedSource.source_type === "dataset_table") {
          const datasets = await fetchDatasets(projectId);
          const ds = datasets.find((d) => d.id === selectedSource.id);
          if (ds?.active_version_id) {
            const schema = await fetchDatasetVersionSchema(selectedSource.id, ds.active_version_id);
            fields = schema.map((col) => col.column_name);
          }
        }
      } catch {
        // Leave fields empty
      } finally {
        setFetchingSchema(false);
      }
    }

    const newSource: SourceNode = {
      source_id: `src-${selectedSource.id}`,
      source_type: sourceType,
      name: selectedSource.name,
      reference_id: selectedSource.id,
      fields,
    };
    onAdd(newSource);
    setSelectedSourceId("");
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
                  className="text-xs text-rose-500 hover:text-rose-700"
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add new source from known catalog */}
      <div className="border-t border-zinc-200 p-4">
        <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Register Source
        </h4>
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-zinc-500">Type</label>
            <select
              value={sourceType}
              onChange={(e) => {
                setSourceType(e.target.value as "dataset_table" | "static_file");
                setSelectedSourceId("");
              }}
              className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none"
            >
              <option value="dataset_table">Dataset Table</option>
              <option value="static_file">Static File</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-500">
              {sourceType === "dataset_table" ? "Dataset" : "Connection"}
            </label>
            {loadingSources ? (
              <p className="mt-1 text-xs text-zinc-400">Loading sources...</p>
            ) : filteredSources.length === 0 ? (
              <p className="mt-1 text-xs text-zinc-400">
                No {sourceType === "dataset_table" ? "datasets" : "static file connections"} available in this project.
              </p>
            ) : (
              <select
                value={selectedSourceId}
                onChange={(e) => setSelectedSourceId(e.target.value)}
                className="mt-1 w-full rounded border border-zinc-300 px-2 py-1.5 text-sm text-zinc-900 focus:border-zinc-500 focus:outline-none"
              >
                <option value="">Select...</option>
                {filteredSources.map((src) => (
                  <option
                    key={src.id}
                    value={src.id}
                    disabled={alreadyRegistered.includes(src.id)}
                  >
                    {src.name}
                    {alreadyRegistered.includes(src.id) ? " (already registered)" : ""}
                  </option>
                ))}
              </select>
            )}
          </div>

          <button
            type="button"
            onClick={handleAdd}
            disabled={!selectedSourceId || fetchingSchema}
            className="w-full rounded-md bg-zinc-900 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {fetchingSchema ? "Loading schema..." : "Add Source"}
          </button>
        </div>
      </div>
    </div>
  );
};
