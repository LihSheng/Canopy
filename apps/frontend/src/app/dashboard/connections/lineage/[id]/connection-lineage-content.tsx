"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchConnection, fetchConnectionLineage } from "@/lib/api/data-source";
import type { Connection } from "@/lib/api/types";
import type { ConnectionLineageEdge, ConnectionLineageNode } from "@/lib/api/data-source";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ROUTES, UI_LABELS } from "@/lib/constants";

const ConnectionLineageContent = ({ connectionId }: { connectionId: string }) => {
  const [connection, setConnection] = useState<Connection | null>(null);
  const [nodes, setNodes] = useState<ConnectionLineageNode[]>([]);
  const [edges, setEdges] = useState<ConnectionLineageEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [conn, lineage] = await Promise.all([
        fetchConnection(connectionId),
        fetchConnectionLineage(connectionId),
      ]);
      setConnection(conn);
      setNodes(lineage.nodes ?? []);
      setEdges(lineage.edges ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load connection lineage");
    } finally {
      setLoading(false);
    }
  }, [connectionId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [load]);

  if (loading) return <LoadingSpinner text={UI_LABELS.loading} />;

  if (error) {
    return (
      <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
        {error}
      </div>
    );
  }

  const source = nodes.find((n) => n.type === "external_source") ?? null;
  const raws = nodes.filter((n) => n.type === "raw_dataset");

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-zinc-900">External Source</h3>
            <p className="mt-1 text-sm text-zinc-600">{source?.label ?? connection?.name ?? connectionId}</p>
          </div>
          <div className="flex items-center gap-3">
            {connection && (
              <Link
                href={`${ROUTES.connections.setupWithSource(connection.source_type)}&connection_id=${encodeURIComponent(connection.id)}&project_id=${encodeURIComponent(connection.project_id)}`}
                className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
              >
                Add tables
              </Link>
            )}
            <div className="text-xs text-zinc-500">
              {connection ? `${connection.source_type} • ${connection.status}` : ""}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-zinc-900">Raw Datasets</h3>
          <div className="text-xs text-zinc-500">
            {raws.length} dataset{raws.length === 1 ? "" : "s"}
          </div>
        </div>

        {raws.length === 0 ? (
          <div className="py-10 text-sm text-zinc-500">No datasets registered for this connection yet</div>
        ) : (
          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            {raws.map((n) => (
              <div
                key={n.id}
                className={
                  n.state === "pending"
                    ? "rounded-lg border border-dashed border-zinc-300 bg-zinc-50 px-3 py-3"
                    : "rounded-lg border border-zinc-200 bg-white px-3 py-3"
                }
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium text-zinc-900">{n.label}</div>
                  {n.state === "pending" ? (
                    <span className="rounded-full border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                      Pending
                    </span>
                  ) : (
                    <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
                      Materialized
                    </span>
                  )}
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-zinc-500">
                  <span>{source?.label ?? "Source"} → {n.label}</span>
                  {n.dataset_id && (
                    <Link
                      href={ROUTES.connections.datasetDetail(n.dataset_id)}
                      className="text-xs font-medium text-zinc-600 hover:text-zinc-900"
                    >
                      Open dataset
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {edges.length > 0 && (
        <div className="rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">Edges</h4>
          <ul className="mt-2 space-y-1 text-sm text-zinc-700">
            {edges.map((e, idx) => (
              <li key={idx}>
                {e.from} → {e.to} <span className="text-xs text-zinc-400">({e.type})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default ConnectionLineageContent;
