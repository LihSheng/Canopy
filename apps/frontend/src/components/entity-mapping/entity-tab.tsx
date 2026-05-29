"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMapping } from "@/lib/api/semantic";
import type {
  Dataset,
  DatasetVersion,
  SemanticMapping,
} from "@/lib/api/types";
import {
  LoadingSpinner,
  ErrorState,
  EmptyState,
} from "@/components/shared";
import { EntityMappingWizard } from "@/components/entity-mapping/entity-mapping-wizard";

type Props = {
  dataset: Dataset;
  versions: DatasetVersion[];
};

export const EntityTab = ({ dataset, versions }: Props) => {
  const activeVersion = versions.find(
    (v) => v.id === dataset.active_version_id
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapping, setMapping] = useState<SemanticMapping | null>(null);
  const [showWizard, setShowWizard] = useState(false);
  const cancelledRef = useRef(false);

  useEffect(() => {
    if (!activeVersion) return;
    cancelledRef.current = false;

    fetchMapping(dataset.id, activeVersion.id)
      .then((currentMapping) => {
        if (!cancelledRef.current) setMapping(currentMapping);
      })
      .catch((err) => {
        if (!cancelledRef.current)
          setError(
            err instanceof Error
              ? err.message
              : "Failed to load entity mapping"
          );
      })
      .finally(() => {
        if (!cancelledRef.current) setLoading(false);
      });

    return () => {
      cancelledRef.current = true;
    };
  }, [dataset.id, activeVersion]);

  const load = useCallback(async () => {
    if (!activeVersion) return;
    cancelledRef.current = false;

    setError(null);
    setLoading(true);
    try {
      const currentMapping = await fetchMapping(
        dataset.id,
        activeVersion.id
      );
      if (!cancelledRef.current) setMapping(currentMapping);
    } catch (err) {
      if (!cancelledRef.current)
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load entity mapping"
        );
    } finally {
      if (!cancelledRef.current) setLoading(false);
    }
  }, [dataset.id, activeVersion]);

  const handleWizardComplete = () => {
    setShowWizard(false);
    load();
  };

  const handleWizardCancel = () => {
    setShowWizard(false);
  };

  if (loading) {
    return <LoadingSpinner text="Loading entity mapping..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={load} />;
  }

  if (!activeVersion) {
    return (
      <EmptyState
        variant="minimal"
        title="No active dataset version"
        description="Create a dataset version before configuring entity mapping."
      />
    );
  }

  // Wizard open
  if (showWizard) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white p-6">
        <h3 className="mb-4 text-sm font-semibold text-zinc-900">
          {mapping ? "Edit Entity Mapping" : "Configure Entity Mapping"}
        </h3>
        <EntityMappingWizard
          datasetId={dataset.id}
          datasetVersionId={activeVersion.id}
          existingMapping={mapping}
          onComplete={handleWizardComplete}
          onCancel={handleWizardCancel}
        />
      </div>
    );
  }

  // Existing mapping view
  if (mapping) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-zinc-200 bg-white p-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900">
                Entity Mapping
              </h3>
              <p className="mt-1 text-xs text-zinc-500">
                v{mapping.version_number} &middot;{" "}
                {mapping.object_type_key}
              </p>
            </div>
            <button
              type="button"
              onClick={() => setShowWizard(true)}
              className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50"
            >
              Edit Mapping
            </button>
          </div>

          {/* Property mapping table */}
          <div className="mt-4 overflow-x-auto rounded-md border border-zinc-200">
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
                    Type
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Primary Key
                  </th>
                  <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Included
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {mapping.properties.map((prop, idx) => (
                  <tr key={idx} className="hover:bg-zinc-50">
                    <td className="px-3 py-2 font-medium text-zinc-900">
                      {prop.source_column}
                    </td>
                    <td className="px-3 py-2 text-zinc-700">
                      {prop.property_name}
                    </td>
                    <td className="px-3 py-2 text-zinc-500">
                      {prop.semantic_type}
                    </td>
                    <td className="px-3 py-2">
                      {prop.is_primary_key ? (
                        <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                          PK
                        </span>
                      ) : (
                        <span className="text-zinc-400">&mdash;</span>
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {prop.included ? (
                        <span className="text-emerald-600">Yes</span>
                      ) : (
                        <span className="text-zinc-400">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // Empty state - no mapping configured
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4 rounded-full bg-zinc-100 p-4">
        <svg
          className="size-8 text-zinc-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"
          />
        </svg>
      </div>
      <p className="text-base font-medium text-zinc-900">
        No entity mapping yet
      </p>
      <p className="mt-1 max-w-sm text-sm text-zinc-500">
        Map dataset columns to a reusable Object Type with primary key and
        friendly property names for use in dashboards and exports.
      </p>
      <button
        type="button"
        onClick={() => setShowWizard(true)}
        className="mt-6 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
      >
        Configure Entity Mapping
      </button>
    </div>
  );
};
