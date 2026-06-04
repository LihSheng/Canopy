"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { fetchEntityByDataset } from "@/lib/api/entities";
import { ROUTES } from "@/lib/constants";
import type { EntityDetail } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared";

type Props = {
  datasetId: string;
};

export const EntityAssociationSummary = ({ datasetId }: Props) => {
  const [entity, setEntity] = useState<EntityDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEntityByDataset(datasetId);
      setEntity(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load entity association");
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white px-4 py-3">
        <LoadingSpinner className="size-4" />
        <span className="text-xs text-zinc-400">Loading entity association...</span>
      </div>
    );
  }

  if (error || !entity) {
    return (
      <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
        <div className="flex items-start justify-between">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
              Entity Association
            </h4>
            <p className="mt-1 text-sm text-zinc-400">
              No entity associated with this dataset.
            </p>
          </div>
          <Link
            href={ROUTES.entities}
            className="shrink-0 text-xs font-medium text-blue-600 hover:text-blue-800"
          >
            Browse Entities
          </Link>
        </div>
      </div>
    );
  }

  const statusBadge = entity.has_published_revision
    ? "Published"
    : entity.has_draft
      ? "Draft"
      : "No revisions";

  const statusColor = entity.has_published_revision
    ? "bg-emerald-100 text-emerald-800"
    : entity.has_draft
      ? "bg-amber-100 text-amber-800"
      : "bg-zinc-100 text-zinc-500";

  return (
    <div className="rounded-lg border border-zinc-200 bg-white px-4 py-3">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            Entity Association
          </h4>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-900">
              {entity.display_name}
            </span>
            <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColor}`}>
              {statusBadge}
              {entity.has_published_revision && entity.published_revision_number && (
                <> v{entity.published_revision_number}</>
              )}
            </span>
          </div>
          <p className="mt-0.5 font-mono text-xs text-zinc-400">
            {entity.object_type_key}
          </p>
        </div>
        <Link
          href={ROUTES.entityDetail(entity.id)}
          className="shrink-0 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50 hover:text-zinc-900"
        >
          Open in Entity Manager
        </Link>
      </div>

      {(entity.published_revision || entity.draft_revision) && (
        <div className="mt-3 border-t border-zinc-100 pt-3">
          <dl className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <dt className="text-zinc-400">Properties</dt>
              <dd className="font-medium text-zinc-900">
                {entity.published_revision?.properties?.length ||
                  entity.draft_revision?.properties?.length ||
                  0}
              </dd>
            </div>
            <div>
              <dt className="text-zinc-400">Source Nodes</dt>
              <dd className="font-medium text-zinc-900">
                {entity.published_revision?.source_nodes?.length ||
                  entity.draft_revision?.source_nodes?.length ||
                  0}
              </dd>
            </div>
            <div>
              <dt className="text-zinc-400">Links</dt>
              <dd className="font-medium text-zinc-900">
                {entity.published_revision?.links?.length ||
                  entity.draft_revision?.links?.length ||
                  0}
              </dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
};
