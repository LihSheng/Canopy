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
  const [selectedSource, setSelectedSource] = useState<SourceType | null>(null);

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
          <SourceCard
            key={source.id}
            source={source}
            onSelect={setSelectedSource}
          />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
          No sources match your search
        </div>
      )}

      {selectedSource && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/30"
          onClick={() => setSelectedSource(null)}
        >
          <div
            className="mx-4 w-full max-w-md rounded-lg bg-white p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-zinc-900">
                {selectedSource.label}
              </h3>
              <button
                onClick={() => setSelectedSource(null)}
                className="text-zinc-400 hover:text-zinc-600"
              >
                <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
                  <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                </svg>
              </button>
            </div>
            <p className="mt-2 text-sm text-zinc-600">{selectedSource.description}</p>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {selectedSource.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600"
                >
                  {tag}
                </span>
              ))}
            </div>
            {selectedSource.enabled ? (
              <Link
                href={`/dashboard/connections/setup?source=${selectedSource.key}`}
                className="mt-4 inline-block rounded-lg bg-zinc-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-zinc-800"
              >
                Connect Source
              </Link>
            ) : (
              <div className="mt-4 rounded-lg bg-zinc-50 px-4 py-3 text-sm text-zinc-500">
                This source is not yet available.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function SourceCard({
  source,
  onSelect,
}: {
  source: SourceType;
  onSelect: (s: SourceType) => void;
}) {
  return (
    <button
      onClick={() => onSelect(source)}
      className={`w-full rounded-lg border p-4 text-left shadow-sm transition-all ${
        source.enabled
          ? "border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-md"
          : "border-zinc-100 bg-zinc-50 opacity-60"
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
    </button>
  );
}
