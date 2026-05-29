"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { fetchConnection, fetchConnectionLineage, updateConnection } from "@/lib/api/data-source";
import type { Connection } from "@/lib/api/types";
import type { ConnectionLineageEdge, ConnectionLineageNode } from "@/lib/api/data-source";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { useToast } from "@/components/shared";
import { ROUTES, UI_LABELS, CONNECTION_STATUS_COLORS } from "@/lib/constants";

const isValidConnectionName = (name: string): string | null => {
  const trimmed = name.trim();
  if (!trimmed) return "Connection name must not be empty";
  if (!/^[A-Za-z]/.test(trimmed)) return "Connection name must start with a letter";
  if (!/^[A-Za-z][A-Za-z0-9 _-]*$/.test(trimmed)) {
    return "Only letters, digits, spaces, hyphens, and underscores are allowed";
  }
  return null;
};

const ConnectionLineageContent = ({ connectionId }: { connectionId: string }) => {
  const [connection, setConnection] = useState<Connection | null>(null);
  const [nodes, setNodes] = useState<ConnectionLineageNode[]>([]);
  const [edges, setEdges] = useState<ConnectionLineageEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Inline rename state
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const editNameRef = useRef<HTMLInputElement | null>(null);
  const toast = useToast();

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

  const handleStartEditName = () => {
    setEditNameValue(connection?.name ?? "");
    setEditingName(true);
    setActionError(null);
    requestAnimationFrame(() => editNameRef.current?.focus());
  };

  const handleSaveName = async () => {
    const validationError = isValidConnectionName(editNameValue);
    if (validationError) {
      setActionError(validationError);
      return;
    }
    const newName = editNameValue.trim();
    if (newName === connection?.name) {
      setEditingName(false);
      setActionError(null);
      return;
    }
    setSavingName(true);
    setActionError(null);
    try {
      await updateConnection(connectionId, { name: newName });
      setEditingName(false);
      toast.success("Connection renamed", `Renamed to "${newName}".`);
      await load();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to rename connection";
      setActionError(message);
      toast.danger("Rename failed", message);
    } finally {
      setSavingName(false);
    }
  };

  const handleNameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSaveName();
    } else if (e.key === "Escape") {
      setEditingName(false);
      setActionError(null);
    }
  };

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
  const displayedName = source?.label ?? connection?.name ?? connectionId;
  const statusColor = CONNECTION_STATUS_COLORS[connection?.status ?? ""] ?? "bg-zinc-100 text-zinc-600";

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-3">
              {editingName ? (
                <div className="flex items-center gap-2">
                  <input
                    ref={editNameRef}
                    type="text"
                    value={editNameValue}
                    onChange={(e) => setEditNameValue(e.target.value)}
                    onKeyDown={handleNameKeyDown}
                    onBlur={() => { if (!savingName) handleSaveName(); }}
                    disabled={savingName}
                    className="w-full max-w-sm rounded-md border border-zinc-300 bg-white px-2 py-1 text-base text-zinc-900 placeholder-zinc-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100 disabled:opacity-50"
                  />
                  {savingName && <LoadingSpinner className="size-4 shrink-0" />}
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleStartEditName}
                  className="group flex items-center gap-1.5 text-lg font-semibold text-zinc-900 hover:text-blue-600"
                  title="Click to rename connection"
                >
                  <span className="truncate">{displayedName}</span>
                  <svg className="size-4 shrink-0 text-zinc-300 transition-colors group-hover:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </button>
              )}
            </div>

            {actionError && (
              <p className="mt-1 text-xs text-red-600">{actionError}</p>
            )}

            {connection && (
              <div className="mt-1.5 flex items-center gap-2 text-xs">
                <span className="text-zinc-500">{connection.source_type}</span>
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${statusColor}`}>
                  {connection.status}
                </span>
              </div>
            )}
          </div>

          <div className="flex shrink-0 items-center gap-3">
            {connection && (
              <Link
                href={`${ROUTES.connections.setupWithSource(connection.source_type)}&connection_id=${encodeURIComponent(connection.id)}&project_id=${encodeURIComponent(connection.project_id)}`}
                className="rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700 transition-colors hover:bg-zinc-50"
              >
                Add tables
              </Link>
            )}
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
                  {n.dataset_id ? (
                    <Link
                      href={ROUTES.connections.datasetDetail(n.dataset_id)}
                      className="text-sm font-medium text-zinc-900 hover:text-blue-600"
                    >
                      {n.label}
                    </Link>
                  ) : (
                    <div className="text-sm font-medium text-zinc-900">{n.label}</div>
                  )}
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
                <div className="mt-2 text-xs text-zinc-500">
                  <span>{source?.label ?? "Source"} → {n.label}</span>
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
