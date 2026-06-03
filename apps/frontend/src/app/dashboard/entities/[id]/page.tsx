"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AnalyticsPageShell } from "@/components/analytics-shell/analytics-page-shell";
import { LoadingSpinner, ErrorState } from "@/components/shared";
import { fetchEntity } from "@/lib/api/entities";
import {
  fetchEntityStatus,
  forkDraft,
  createInitialRevision,
  publishDraft,
  discardDraft,
} from "@/lib/api/entities";
import { ROUTES } from "@/lib/constants";
import type {
  EntityDetail,
  EntityStatus,
  EntityRevisionDetail,
  PropertyMapping,
  ComputedProperty,
  EntityLink,
  EntityRevisionProperty,
} from "@/lib/api/types";

const EntityDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [entity, setEntity] = useState<EntityDetail | null>(null);
  const [status, setStatus] = useState<EntityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, st] = await Promise.all([
        fetchEntity(id),
        fetchEntityStatus(id),
      ]);
      setEntity(data);
      setStatus(st);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load entity");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreateInitialDraft = async () => {
    setActionLoading("create");
    try {
      await createInitialRevision(id, {});
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create initial draft");
    } finally {
      setActionLoading(null);
    }
  };

  const handleForkDraft = async () => {
    setActionLoading("fork");
    try {
      await forkDraft(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create draft");
    } finally {
      setActionLoading(null);
    }
  };

  const handlePublish = async () => {
    setActionLoading("publish");
    try {
      await publishDraft(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to publish draft");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDiscardDraft = async () => {
    setActionLoading("discard");
    try {
      await discardDraft(id);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to discard draft");
    } finally {
      setActionLoading(null);
    }
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

  const semanticTypeLabel = (t: string): string => {
    const labels: Record<string, string> = {
      string: "String",
      integer: "Integer",
      number: "Number",
      boolean: "Boolean",
      datetime: "DateTime",
      date: "Date",
    };
    return labels[t] || t;
  };

  // Determine what to render: published revision > draft revision > legacy mapping
  const effectiveRevision: EntityRevisionDetail | null =
    entity?.published_revision || entity?.draft_revision || null;
  const effectiveMapping = effectiveRevision ? null : entity?.mapping;

  // Effective source nodes (revision has typed source_nodes; mapping has raw)
  const effectiveSources = effectiveRevision?.source_nodes ?? effectiveMapping?.source_nodes ?? [];
  // Effective properties (revision or mapping)
  const effectiveProperties = effectiveRevision?.properties ?? effectiveMapping?.properties ?? [];
  // Effective computed properties
  const effectiveComputed = effectiveRevision?.computed_properties ?? effectiveMapping?.computed_properties ?? [];
  // Effective links
  const effectiveLinks = effectiveRevision?.links ?? effectiveMapping?.links ?? [];

  const hasContent = effectiveRevision || effectiveMapping;

  const isRevisionProperty = (
    prop: EntityRevisionProperty | PropertyMapping
  ): prop is EntityRevisionProperty => {
    return "property_id" in prop;
  };

  return (
    <AnalyticsPageShell
      title={entity?.display_name || "Entity Detail"}
      contextText={entity?.object_type_key || ""}
      breadcrumbItems={[
        { label: "Entities", href: ROUTES.entities },
        { label: entity?.display_name || "..." },
      ]}
    >
      {loading && <LoadingSpinner text="Loading entity..." />}

      {error && <ErrorState message={error} onRetry={load} />}

      {!loading && !error && entity && (
        <div className="space-y-6">
          {/* Header section */}
          <div className="rounded-lg border border-zinc-200 bg-white p-4">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-lg font-semibold text-zinc-900">
                  {entity.display_name}
                </h2>
                <p className="mt-1 text-sm text-zinc-500">
                  <span className="font-mono text-xs">{entity.object_type_key}</span>
                </p>
                {entity.description && (
                  <p className="mt-2 text-sm text-zinc-600">{entity.description}</p>
                )}
              </div>

              {/* Revision action buttons */}
              <div className="flex items-center gap-2">
                {status && (
                  <>
                    {!status.has_published && !status.has_draft && (
                      <button
                        type="button"
                        onClick={handleCreateInitialDraft}
                        disabled={actionLoading === "create"}
                        className="shrink-0 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50"
                      >
                        {actionLoading === "create" ? "Creating..." : "Create Draft"}
                      </button>
                    )}
                    {status.has_draft && (
                      <>
                        <button
                          type="button"
                          onClick={handlePublish}
                          disabled={actionLoading === "publish"}
                          className="shrink-0 rounded-md bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
                        >
                          {actionLoading === "publish" ? "Publishing..." : "Publish"}
                        </button>
                        <button
                          type="button"
                          onClick={handleDiscardDraft}
                          disabled={actionLoading === "discard"}
                          className="shrink-0 rounded-md border border-red-200 bg-white px-3 py-1.5 text-xs font-medium text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50"
                        >
                          {actionLoading === "discard" ? "Discarding..." : "Discard Draft"}
                        </button>
                      </>
                    )}
                    {status.has_published && !status.has_draft && (
                      <button
                        type="button"
                        onClick={handleForkDraft}
                        disabled={actionLoading === "fork"}
                        className="shrink-0 rounded-md border border-zinc-200 bg-white px-3 py-1.5 text-xs font-medium text-zinc-700 transition-colors hover:bg-zinc-50 disabled:opacity-50"
                      >
                        {actionLoading === "fork" ? "Creating..." : "Edit (New Draft)"}
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>

            {/* Revision status badges */}
            {status && (
              <div className="mt-3 flex flex-wrap items-center gap-2">
                {status.has_published ? (
                  <span className="inline-block rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                    Published v{status.published_revision_number}
                  </span>
                ) : (
                  <span className="inline-block rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-500">
                    No published version
                  </span>
                )}
                {status.has_draft ? (
                  <span className="inline-block rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-800">
                    Draft v{status.draft_revision_number}
                    {status.lock_holder_id && (
                      <span className="ml-1 text-amber-600">
                        (locked)
                      </span>
                    )}
                  </span>
                ) : (
                  <span className="inline-block rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-medium text-zinc-400">
                    No draft
                  </span>
                )}
              </div>
            )}

            <dl className="mt-4 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
              <div>
                <dt className="text-xs text-zinc-400">Backing Dataset</dt>
                <dd className="font-medium text-zinc-900">
                  {entity.dataset_name ? (
                    <a
                      href={ROUTES.connections.datasetDetail(entity.mapping?.dataset_id || "")}
                      className="text-zinc-900 underline hover:text-zinc-600"
                    >
                      {entity.dataset_name}
                    </a>
                  ) : (
                    "\u2014"
                  )}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-400">Mapping Version</dt>
                <dd className="font-medium text-zinc-900">
                  {entity.mapping
                    ? `v${entity.mapping.version_number}`
                    : "\u2014"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-400">Created</dt>
                <dd className="font-medium text-zinc-900">
                  {formatDate(entity.created_at)}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-zinc-400">Updated</dt>
                <dd className="font-medium text-zinc-900">
                  {formatDate(entity.updated_at)}
                </dd>
              </div>
            </dl>
          </div>

          {/* Entity detail sections — prefers revision over legacy mapping */}
          {hasContent ? (
            <>
              {/* Properties */}
              <section className="rounded-lg border border-zinc-200 bg-white">
                <div className="border-b border-zinc-100 px-4 py-3">
                  <h3 className="text-sm font-semibold text-zinc-900">
                    Properties
                    <span className="ml-1.5 text-xs font-normal text-zinc-400">
                      ({effectiveProperties.length})
                    </span>
                  </h3>
                </div>
                {effectiveProperties.length === 0 ? (
                  <p className="px-4 py-6 text-sm text-zinc-400">
                    No properties mapped.
                  </p>
                ) : (
                  <table className="min-w-full divide-y divide-zinc-100 text-sm">
                    <thead>
                      <tr className="bg-zinc-50">
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Property
                        </th>
                        {isRevisionProperty(effectiveProperties[0]) ? (
                          <>
                            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              Key
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              Type
                            </th>
                            <th className="px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              Req
                            </th>
                            <th className="px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              PK
                            </th>
                          </>
                        ) : (
                          <>
                            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              Source Column
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              Type
                            </th>
                            <th className="px-4 py-2 text-center text-xs font-semibold uppercase tracking-wider text-zinc-500">
                              PK
                            </th>
                          </>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {isRevisionProperty(effectiveProperties[0])
                        ? (effectiveProperties as EntityRevisionProperty[]).map((p) => (
                            <tr key={p.property_id} className="hover:bg-zinc-50">
                              <td className="px-4 py-2 font-medium text-zinc-900">
                                {p.display_name}
                              </td>
                              <td className="px-4 py-2 font-mono text-xs text-zinc-500">
                                {p.property_key}
                              </td>
                              <td className="px-4 py-2 text-zinc-500">
                                <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
                                  {semanticTypeLabel(p.semantic_type)}
                                </span>
                              </td>
                              <td className="px-4 py-2 text-center">
                                {p.is_required ? (
                                  <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
                                    Req
                                  </span>
                                ) : (
                                  <span className="text-zinc-300">\u2014</span>
                                )}
                              </td>
                              <td className="px-4 py-2 text-center">
                                {p.is_primary_key ? (
                                  <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                                    PK
                                  </span>
                                ) : (
                                  <span className="text-zinc-300">\u2014</span>
                                )}
                              </td>
                            </tr>
                          ))
                        : (effectiveProperties as PropertyMapping[]).map((p, i) => (
                            <tr key={i} className="hover:bg-zinc-50">
                              <td className="px-4 py-2 font-medium text-zinc-900">
                                {p.property_name}
                              </td>
                              <td className="px-4 py-2 font-mono text-xs text-zinc-500">
                                {p.source_column}
                              </td>
                              <td className="px-4 py-2 text-zinc-500">
                                <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
                                  {semanticTypeLabel(p.semantic_type)}
                                </span>
                              </td>
                              <td className="px-4 py-2 text-center">
                                {p.is_primary_key ? (
                                  <span className="inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
                                    PK
                                  </span>
                                ) : (
                                  <span className="text-zinc-300">\u2014</span>
                                )}
                              </td>
                            </tr>
                          ))}
                    </tbody>
                  </table>
                )}
              </section>

              {/* Computed Properties */}
              {effectiveComputed.length > 0 && (
                <section className="rounded-lg border border-zinc-200 bg-white">
                  <div className="border-b border-zinc-100 px-4 py-3">
                    <h3 className="text-sm font-semibold text-zinc-900">
                      Computed Properties
                      <span className="ml-1.5 text-xs font-normal text-zinc-400">
                        ({effectiveComputed.length})
                      </span>
                    </h3>
                  </div>
                  <table className="min-w-full divide-y divide-zinc-100 text-sm">
                    <thead>
                      <tr className="bg-zinc-50">
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Property
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Type / Kind
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Expression
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {effectiveComputed.map((cp) => (
                        <tr key={cp.id} className="hover:bg-zinc-50">
                          <td className="px-4 py-2 font-medium text-zinc-900">
                            {cp.property_name}
                          </td>
                          <td className="px-4 py-2 text-zinc-500">
                            <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
                              {semanticTypeLabel(cp.semantic_type)}
                            </span>
                            <span className="ml-1.5 text-xs text-zinc-400">
                              {cp.composition_kind}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-xs font-mono text-zinc-500 max-w-xs truncate">
                            {cp.expression || "\u2014"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              )}

              {/* Links */}
              <section className="rounded-lg border border-zinc-200 bg-white">
                <div className="border-b border-zinc-100 px-4 py-3">
                  <h3 className="text-sm font-semibold text-zinc-900">
                    Links
                    <span className="ml-1.5 text-xs font-normal text-zinc-400">
                      ({effectiveLinks.length})
                    </span>
                  </h3>
                </div>
                {effectiveLinks.length === 0 ? (
                  <p className="px-4 py-6 text-sm text-zinc-400">
                    No linked entities.
                  </p>
                ) : (
                  <table className="min-w-full divide-y divide-zinc-100 text-sm">
                    <thead>
                      <tr className="bg-zinc-50">
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Link
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Source Property
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Cardinality
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {effectiveLinks.map((link) => (
                        <tr key={link.link_id} className="hover:bg-zinc-50">
                          <td className="px-4 py-2 font-medium text-zinc-900">
                            {link.display_name}
                          </td>
                          <td className="px-4 py-2 font-mono text-xs text-zinc-500">
                            {link.source_property_key}
                          </td>
                          <td className="px-4 py-2 text-zinc-500">
                            <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
                              {link.cardinality}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </section>

              {/* Source nodes (revision-only section) */}
              {effectiveRevision && effectiveSources.length > 0 && (
                <section className="rounded-lg border border-zinc-200 bg-white">
                  <div className="border-b border-zinc-100 px-4 py-3">
                    <h3 className="text-sm font-semibold text-zinc-900">
                      Source Bindings
                      <span className="ml-1.5 text-xs font-normal text-zinc-400">
                        ({effectiveSources.length})
                      </span>
                    </h3>
                  </div>
                  <table className="min-w-full divide-y divide-zinc-100 text-sm">
                    <thead>
                      <tr className="bg-zinc-50">
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Source
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Type
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
                          Fields
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-100">
                      {effectiveSources.map((sn) => (
                        <tr key={sn.source_id} className="hover:bg-zinc-50">
                          <td className="px-4 py-2 font-medium text-zinc-900">
                            {sn.name}
                          </td>
                          <td className="px-4 py-2 text-zinc-500">
                            <span className="inline-block rounded-full border border-zinc-200 px-2 py-0.5 text-xs font-medium text-zinc-600">
                              {sn.source_type}
                            </span>
                          </td>
                          <td className="px-4 py-2 text-xs font-mono text-zinc-500">
                            {sn.fields?.join(", ") || "\u2014"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </section>
              )}
            </>
          ) : (
            <div className="rounded-lg border border-zinc-200 bg-white px-4 py-8 text-center text-sm text-zinc-400">
              No mapping configured for this entity.
            </div>
          )}
        </div>
      )}
    </AnalyticsPageShell>
  );
};

export default EntityDetailPage;
