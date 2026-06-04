"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchRevisions, fetchRevision } from "@/lib/api/entities";
import type { EntityRevision } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared";

type Props = {
  entityId: string;
  publishedRevisionId: string | null;
  onRevert?: (revision: EntityRevision) => void;
};

const statusStyles: Record<string, string> = {
  published: "bg-emerald-100 text-emerald-800",
  draft: "bg-amber-100 text-amber-800",
  archived: "bg-zinc-100 text-zinc-500",
};

export const EntityVersionHistory = ({ entityId, publishedRevisionId, onRevert }: Props) => {
  const [revisions, setRevisions] = useState<EntityRevision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedRevision, setSelectedRevision] = useState<EntityRevision | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRevisions(entityId);
      setRevisions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load version history");
    } finally {
      setLoading(false);
    }
  }, [entityId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleSelectRevision = async (revision: EntityRevision) => {
    // If we already have the full detail (from the list), just select it
    // Otherwise fetch the single revision for full detail
    if (selectedRevision?.id === revision.id) {
      setSelectedRevision(null);
      return;
    }
    setDetailLoading(true);
    setDetailError(null);
    try {
      const detail = await fetchRevision(entityId, revision.id);
      setSelectedRevision(detail);
    } catch (err) {
      setDetailError(err instanceof Error ? err.message : "Failed to load revision detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return "\u2014";
    try {
      return new Date(dateStr).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "\u2014";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner className="size-5" />
        <span className="ml-2 text-sm text-zinc-400">Loading version history...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
        {error}
        <button
          type="button"
          onClick={load}
          className="ml-2 font-medium underline hover:text-red-600"
        >
          Retry
        </button>
      </div>
    );
  }

  if (revisions.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white px-4 py-6 text-center text-sm text-zinc-400">
        No version history yet. Publish a revision to create history.
      </div>
    );
  }

  // Only show published/archived revisions in history (exclude active draft)
  // Unless there are no published/archived revisions, then show all
  const historyRevisions = revisions.filter(
    (r) => r.status !== "draft"
  );
  const displayRevisions = historyRevisions.length > 0 ? historyRevisions : revisions;

  return (
    <div className="space-y-3">
      <div className="overflow-hidden rounded-lg border border-zinc-200">
        <table className="min-w-full divide-y divide-zinc-200 text-sm">
          <thead>
            <tr className="bg-zinc-50">
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Version
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Status
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Properties
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Sources
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Links
              </th>
              <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Published
              </th>
              {onRevert && (
                <th className="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-100">
            {displayRevisions.map((revision) => {
              const isActivePublished =
                revision.status === "published" &&
                revision.id === publishedRevisionId;
              const isSelected = selectedRevision?.id === revision.id;

              return (
                <tr
                  key={revision.id}
                  className={`hover:bg-zinc-50 cursor-pointer transition-colors ${
                    isSelected ? "bg-blue-50" : ""
                  }`}
                  onClick={() => handleSelectRevision(revision)}
                >
                  <td className="px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                          isActivePublished
                            ? "bg-zinc-900 text-white"
                            : "bg-zinc-100 text-zinc-700"
                        }`}
                      >
                        v{revision.revision_number}
                      </span>
                      {isActivePublished && (
                        <span className="text-xs font-medium text-emerald-600">
                          Active
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                        statusStyles[revision.status] || "bg-zinc-100 text-zinc-600"
                      }`}
                    >
                      {revision.status}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-zinc-700">
                    {revision.properties?.length || 0}
                  </td>
                  <td className="px-4 py-2 text-zinc-700">
                    {revision.source_nodes?.length || 0}
                  </td>
                  <td className="px-4 py-2 text-zinc-700">
                    {revision.links?.length || 0}
                  </td>
                  <td className="px-4 py-2 text-zinc-500 text-xs">
                    {formatDate(revision.published_at)}
                  </td>
                  {onRevert && revision.status !== "draft" && (
                    <td className="px-4 py-2 text-right">
                      {!isActivePublished ? (
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onRevert(revision);
                          }}
                          className="rounded-md border border-zinc-200 px-3 py-1 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-100"
                        >
                          Revert
                        </button>
                      ) : (
                        <span className="text-xs text-zinc-400">Current</span>
                      )}
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Revision detail panel */}
      {detailLoading && (
        <div className="flex items-center justify-center py-4">
          <LoadingSpinner className="size-4" />
          <span className="ml-2 text-xs text-zinc-400">Loading revision detail...</span>
        </div>
      )}

      {detailError && (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-800">
          {detailError}
        </div>
      )}

      {selectedRevision && !detailLoading && (
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-sm font-semibold text-zinc-900">
              Revison v{selectedRevision.revision_number} Detail
            </h4>
            <button
              type="button"
              onClick={() => setSelectedRevision(null)}
              className="text-xs font-medium text-zinc-400 hover:text-zinc-600"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            {/* Properties */}
            <div>
              <h5 className="mb-1 font-medium text-zinc-600">
                Properties ({selectedRevision.properties?.length || 0})
              </h5>
              {selectedRevision.properties && selectedRevision.properties.length > 0 ? (
                <ul className="space-y-0.5">
                  {selectedRevision.properties.map((p) => (
                    <li key={p.property_id} className="text-zinc-700">
                      <span className="font-medium">{p.display_name}</span>
                      <span className="ml-1 text-zinc-400">({p.property_key})</span>
                      {p.is_required && (
                        <span className="ml-1 text-amber-600">*</span>
                      )}
                      {p.is_primary_key && (
                        <span className="ml-1 rounded bg-amber-100 px-1 text-[10px] text-amber-700">
                          PK
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-zinc-400">No properties</p>
              )}
            </div>

            {/* Source nodes */}
            <div>
              <h5 className="mb-1 font-medium text-zinc-600">
                Sources ({selectedRevision.source_nodes?.length || 0})
              </h5>
              {selectedRevision.source_nodes && selectedRevision.source_nodes.length > 0 ? (
                <ul className="space-y-0.5">
                  {selectedRevision.source_nodes.map((sn, i) => (
                    <li key={sn.source_id || i} className="text-zinc-700">
                      <span className="font-medium">{sn.name}</span>
                      <span className="ml-1 text-zinc-400">({sn.source_type})</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-zinc-400">No sources</p>
              )}
            </div>

            {/* Links */}
            <div>
              <h5 className="mb-1 font-medium text-zinc-600">
                Links ({selectedRevision.links?.length || 0})
              </h5>
              {selectedRevision.links && selectedRevision.links.length > 0 ? (
                <ul className="space-y-0.5">
                  {selectedRevision.links.map((link) => (
                    <li key={link.link_id} className="text-zinc-700">
                      <span className="font-medium">{link.display_name}</span>
                      <span className="ml-1 text-zinc-400">
                        ({link.source_property_key} &rarr; {link.target_property_key})
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-zinc-400">No links</p>
              )}
            </div>

            {/* Timestamps */}
            <div>
              <h5 className="mb-1 font-medium text-zinc-600">Timestamps</h5>
              <dl className="space-y-0.5">
                <div>
                  <dt className="inline text-zinc-400">Created: </dt>
                  <dd className="inline text-zinc-700">{formatDate(selectedRevision.created_at)}</dd>
                </div>
                <div>
                  <dt className="inline text-zinc-400">Published: </dt>
                  <dd className="inline text-zinc-700">{formatDate(selectedRevision.published_at)}</dd>
                </div>
                <div>
                  <dt className="inline text-zinc-400">Forked from: </dt>
                  <dd className="inline text-zinc-700">
                    {selectedRevision.forked_from_revision_id
                      ? selectedRevision.forked_from_revision_id.slice(0, 8)
                      : "\u2014"}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
