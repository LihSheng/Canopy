"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchSourceTypes } from "@/lib/api/data-source";
import type { SourceType } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";

export default function SourceCatalogContent() {
  const [sources, setSources] = useState<SourceType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSourceTypes();
      setSources(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = sources.filter(
    (s) =>
      s.label.toLowerCase().includes(search.toLowerCase()) ||
      s.tags.some((t) => t.toLowerCase().includes(search.toLowerCase())),
  );

  if (loading) return <LoadingSpinner text="Loading source catalog..." />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-6">
      <div className="relative max-w-md">
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400"
        >
          <path
            fillRule="evenodd"
            d="M9 3.5a5.5 5.5 0 100 11 5.5 5.5 0 000-11zM2 9a7 7 0 1112.452 4.391l3.328 3.329a.75.75 0 11-1.06 1.06l-3.329-3.328A7 7 0 012 9z"
            clipRule="evenodd"
          />
        </svg>
        <input
          type="text"
          placeholder="Search sources..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-zinc-200 py-2 pl-9 pr-3 text-sm text-zinc-900 placeholder-zinc-400 focus:border-zinc-400 focus:outline-none"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filtered.map((source) => (
          <SourceCard key={source.id} source={source} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
          No sources match your search
        </div>
      )}
    </div>
  );
}

function SourceCard({ source }: { source: SourceType }) {
  return (
    <Link
      href={source.enabled ? `/dashboard/connections/setup?source=${source.key}` : "#"}
      className={`block w-full rounded-lg border p-4 text-left shadow-sm transition-all ${
        source.enabled
          ? "border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-md"
          : "border-zinc-100 bg-zinc-50 opacity-60 cursor-not-allowed"
      }`}
    >
      <div className="flex items-center justify-between">
        <h3
          className={`text-sm font-semibold ${
            source.enabled ? "text-zinc-900" : "text-zinc-500"
          }`}
        >
          {source.label}
        </h3>
        {!source.enabled && (
          <span className="rounded-full bg-zinc-200 px-2 py-0.5 text-[10px] font-medium text-zinc-500">
            Coming Soon
          </span>
        )}
      </div>
      <p className="mt-1 text-xs text-zinc-500 line-clamp-2">{source.description}</p>
      {source.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {source.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded-full bg-zinc-100 px-1.5 py-0.5 text-[10px] text-zinc-500"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </Link>
  );
}
