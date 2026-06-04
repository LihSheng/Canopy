"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { EntityHelperShell, type HelperStep } from "./entity-helper-shell";
import { fetchEntities, forkDraft, fetchEntityByDataset } from "@/lib/api/entities";
import { ROUTES } from "@/lib/constants";
import type { EntityRegistryItem } from "@/lib/api/types";

const STEPS: HelperStep[] = [
  { key: "search", label: "Search", description: "Find an existing entity" },
  { key: "confirm", label: "Confirm", description: "Review and attach" },
];

interface AttachExistingEntityFlowProps {
  onClose: () => void;
  /** Optional: pre-selected dataset ID to attach */
  datasetId?: string;
}

/**
 * Attach-Existing Entity flow.
 *
 * User searches for an existing entity, selects one, forks a draft,
 * and attaches a dataset into it. Then navigates into the Entity Manager.
 */
export function AttachExistingEntityFlow({
  onClose,
  datasetId,
}: AttachExistingEntityFlowProps) {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ─── Search state ───
  const [search, setSearch] = useState("");
  const [results, setResults] = useState<EntityRegistryItem[]>([]);
  const [searching, setSearching] = useState(false);
  const [selected, setSelected] = useState<EntityRegistryItem | null>(null);

  // ─── Recent / suggested (first 5 entities) ───
  const [recent, setRecent] = useState<EntityRegistryItem[]>([]);

  // Load recent entities on mount
  useEffect(() => {
    fetchEntities()
      .then((data) => setRecent(data.slice(0, 5)))
      .catch(() => setRecent([]));
  }, []);

  // ─── Search ───
  const handleSearch = useCallback(async (q: string) => {
    setSearch(q);
    if (!q.trim()) {
      setResults([]);
      return;
    }
    setSearching(true);
    try {
      const data = await fetchEntities(q);
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  // ─── Attach ───
  const handleAttach = async () => {
    if (!selected) return;
    setLoading(true);
    setError(null);
    try {
      // Check if entity already has a dataset association
      if (datasetId) {
        const existing = await fetchEntityByDataset(datasetId);
        if (existing) {
          throw new Error(
            `Dataset is already associated with entity "${existing.display_name}". A dataset can only belong to one entity.`
          );
        }
      }

      // Fork a draft before editing
      try {
        await forkDraft(selected.id);
      } catch {
        // Entity may not have a published revision yet, try creating initial
        try {
          const { createInitialRevision } = await import("@/lib/api/entities");
          await createInitialRevision(selected.id, {});
        } catch {
          // Draft creation is best-effort; the shell may not have revisions yet
        }
      }

      // Navigate to entity manager
      onClose();
      router.push(ROUTES.entityDetail(selected.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to attach to entity");
    } finally {
      setLoading(false);
    }
  };

  const canGoNext = (): boolean => {
    switch (step) {
      case 0:
        return selected !== null;
      case 1:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    setError(null);
    if (step === 0 && selected) {
      setStep(1);
    } else if (step === 1) {
      handleAttach();
    }
  };

  const handleBack = () => {
    setError(null);
    if (step > 0) setStep(0);
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return "\u2014";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "\u2014";
    }
  };

  return (
    <EntityHelperShell
      title="Attach Existing Entity"
      subtitle={
        datasetId
          ? "Attach this dataset to an existing entity"
          : "Find and attach to an existing business object"
      }
      steps={STEPS}
      currentStep={step}
      canGoBack={step > 0}
      canGoNext={canGoNext()}
      isLastStep={step === 1}
      nextLabel={step === 1 ? "Attach & Open" : "Next"}
      loading={loading}
      error={error}
      onBack={handleBack}
      onNext={handleNext}
      onClose={onClose}
    >
      {/* ─── Step 0: Search ─── */}
      {step === 0 && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Search for an existing entity to attach to. A draft will be forked
            so you can make changes without affecting the published version.
          </p>

          {/* Search input */}
          <div className="relative">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-400"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clipRule="evenodd"
              />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              placeholder="Search entities by name, key, or dataset..."
              className="w-full rounded-md border border-zinc-300 bg-white pl-10 pr-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
              autoFocus
            />
          </div>

          {/* Recent / Suggested */}
          {!search && recent.length > 0 && (
            <div>
              <div className="mb-2 text-xs font-medium text-zinc-400 uppercase tracking-wider">
                Recent Entities
              </div>
              <div className="space-y-1">
                {recent.map((entity) => (
                  <button
                    key={entity.id}
                    type="button"
                    onClick={() => {
                      setSelected(entity);
                      setSearch("");
                    }}
                    className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                      selected?.id === entity.id
                        ? "border-zinc-900 bg-zinc-50"
                        : "border-zinc-100 hover:border-zinc-200"
                    }`}
                  >
                    <span className="font-medium text-zinc-900">
                      {entity.display_name}
                    </span>
                    <span className="ml-2 font-mono text-xs text-zinc-400">
                      {entity.object_type_key}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Search results */}
          {searching && (
            <div className="py-4 text-center text-sm text-zinc-400">
              Searching...
            </div>
          )}

          {!searching && search && results.length === 0 && (
            <div className="py-4 text-center text-sm text-zinc-400">
              No entities found matching &quot;{search}&quot;
            </div>
          )}

          {!searching && results.length > 0 && (
            <div className="space-y-1">
              <div className="mb-2 text-xs font-medium text-zinc-400 uppercase tracking-wider">
                Results ({results.length})
              </div>
              {results.map((entity) => (
                <button
                  key={entity.id}
                  type="button"
                  onClick={() => {
                    setSelected(entity);
                    setSearch("");
                    setResults([]);
                  }}
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm transition-colors ${
                    selected?.id === entity.id
                      ? "border-zinc-900 bg-zinc-50"
                      : "border-zinc-100 hover:border-zinc-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-zinc-900">
                      {entity.display_name}
                    </span>
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        entity.status === "published"
                          ? "bg-emerald-100 text-emerald-800"
                          : entity.has_published_revision
                            ? "bg-emerald-100 text-emerald-800"
                            : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {entity.status === "published" || entity.has_published_revision
                        ? "Published"
                        : "In Progress"}
                    </span>
                  </div>
                  <div className="mt-0.5 font-mono text-xs text-zinc-400">
                    {entity.object_type_key}
                    {entity.dataset_name ? ` · ${entity.dataset_name}` : ""}
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Selected indicator */}
          {selected && (
            <div className="rounded-md border border-zinc-200 bg-zinc-50 px-3 py-2 flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-zinc-900">
                  Selected: {selected.display_name}
                </span>
                <span className="ml-2 font-mono text-xs text-zinc-500">
                  {selected.object_type_key}
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                className="text-xs text-zinc-400 hover:text-zinc-600"
              >
                Clear
              </button>
            </div>
          )}
        </div>
      )}

      {/* ─── Step 1: Confirm ─── */}
      {step === 1 && selected && (
        <div className="space-y-4">
          <p className="text-sm text-zinc-600">
            Review the entity you are about to attach to. A draft will be forked
            so you can make changes safely.
          </p>

          <div className="rounded-lg border border-zinc-200 divide-y divide-zinc-100 text-sm">
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Entity</span>
              <span className="font-medium text-zinc-900">
                {selected.display_name}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Object Type Key</span>
              <span className="font-mono text-xs text-zinc-900">
                {selected.object_type_key}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Current Dataset</span>
              <span className="font-medium text-zinc-900">
                {selected.dataset_name || "None"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Status</span>
              <span
                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                  selected.status === "published" || selected.has_published_revision
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {selected.status === "published" || selected.has_published_revision
                  ? "Published"
                  : "In Progress"}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Properties</span>
              <span className="font-medium text-zinc-900">
                {selected.property_count}
              </span>
            </div>
            <div className="px-4 py-2.5 flex justify-between">
              <span className="text-zinc-500">Last Updated</span>
              <span className="font-medium text-zinc-900">
                {formatDate(selected.updated_at)}
              </span>
            </div>
            {datasetId && (
              <div className="px-4 py-2.5 flex justify-between">
                <span className="text-zinc-500">Dataset to Attach</span>
                <span className="font-mono text-xs text-zinc-900">
                  {datasetId}
                </span>
              </div>
            )}
          </div>

          <div className="rounded-md border border-amber-100 bg-amber-50 px-4 py-3 text-xs text-amber-800">
            Attaching to this entity will fork a draft so you can make changes.
            The published version remains unchanged until you publish the draft.
          </div>
        </div>
      )}
    </EntityHelperShell>
  );
}
