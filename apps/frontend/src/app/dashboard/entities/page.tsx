"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { LoadingSpinner, ErrorState, EmptyState } from "@/components/shared";
import { fetchEntities } from "@/lib/api/entities";
import { ROUTES } from "@/lib/constants";
import type { EntityRegistryItem } from "@/lib/api/types";

const EntityRegistryPage = () => {
  const router = useRouter();
  const [entities, setEntities] = useState<EntityRegistryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEntities(search || undefined);
      setEntities(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load entities");
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSearch = (value: string) => {
    setSearch(value);
  };

  const handleRowClick = (id: string) => {
    router.push(ROUTES.entityDetail(id));
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
    <AnalyticsPageShell title="Entities" contextText="Entity registry">
      <div className="space-y-4">
        {/* Search bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1 max-w-sm">
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
              placeholder="Search entities by name, key, or dataset..."
              value={search}
              onChange={(e) => handleSearch(e.target.value)}
              className="w-full rounded-md border border-zinc-300 bg-white pl-10 pr-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
            />
          </div>
        </div>

        {loading && <LoadingSpinner text="Loading entities..." />}

        {error && <ErrorState message={error} onRetry={load} />}

        {!loading && !error && entities.length === 0 && (
          <EmptyState
            variant="minimal"
            title="No entities found"
            description={
              search
                ? `No entities match "${search}". Try a different search term.`
                : "Create an entity mapping from a dataset to see it here."
            }
          />
        )}

        {!loading && !error && entities.length > 0 && (
          <div className="rounded-lg border border-zinc-200 overflow-hidden">
            <table className="min-w-full divide-y divide-zinc-200 text-sm">
              <thead>
                <tr className="bg-zinc-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Entity
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Key
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Dataset
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Properties
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Links
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">
                    Updated
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {entities.map((entity) => (
                  <tr
                    key={entity.id}
                    onClick={() => handleRowClick(entity.id)}
                    className="cursor-pointer transition-colors hover:bg-zinc-50"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium text-zinc-900">
                        {entity.display_name}
                      </div>
                      {entity.description && (
                        <div className="mt-0.5 text-xs text-zinc-500 truncate max-w-xs">
                          {entity.description}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-zinc-600 font-mono text-xs">
                      {entity.object_type_key}
                    </td>
                    <td className="px-4 py-3 text-zinc-500">
                      {entity.dataset_name || "\u2014"}
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-600">
                      {entity.property_count}
                    </td>
                    <td className="px-4 py-3 text-center text-zinc-600">
                      {entity.link_count}
                    </td>
                    <td className="px-4 py-3 text-right text-xs text-zinc-500">
                      {formatDate(entity.mapping_updated_at || entity.updated_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AnalyticsPageShell>
  );
};

export default EntityRegistryPage;
