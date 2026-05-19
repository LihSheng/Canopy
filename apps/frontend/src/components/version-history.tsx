import type { DatasetVersion } from "@/lib/api/types";

type Props = {
  versions: DatasetVersion[];
  activeVersionId: string | null | undefined;
  onDeleteVersion?: (version: DatasetVersion) => void | Promise<void>;
  deletingVersionId?: string | null;
  onUploadVersion?: () => void;
};

const statusStyles: Record<string, string> = {
  ready: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  pending: "bg-amber-100 text-amber-800",
  processing: "bg-blue-100 text-blue-800",
};

export function VersionHistory({
  versions = [],
  activeVersionId,
  onDeleteVersion,
  deletingVersionId = null,
  onUploadVersion,
}: Props) {
  if (!versions || versions.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No versions yet
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        {onDeleteVersion && activeVersionId && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            Active version is locked. Use Delete Version only for non-active snapshots.
          </div>
        )}
        {onUploadVersion && (
          <button
            type="button"
            onClick={onUploadVersion}
            className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            Upload New Version
          </button>
        )}
      </div>
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
              Rows
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Columns
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Issues
            </th>
            <th className="px-4 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Created
            </th>
            {onDeleteVersion && (
              <th className="px-4 py-2 text-right text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {versions.map((version) => {
            const isActive = version.id === activeVersionId;
            const isSuperseded = !isActive && version.status === "ready";
            const isFailed = version.status === "failed";
            return (
              <tr key={version.id} className="hover:bg-zinc-50">
                <td className="px-4 py-2">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      isActive
                        ? "bg-zinc-900 text-white"
                        : isSuperseded
                          ? "bg-zinc-200 text-zinc-600"
                          : "bg-zinc-100 text-zinc-700"
                    }`}
                  >
                    v{version.version_number}
                  </span>
                  {isActive && (
                    <span className="ml-2 text-xs font-medium text-zinc-500">Active</span>
                  )}
                  {isSuperseded && (
                    <span className="ml-2 text-xs font-medium text-zinc-400">Superseded</span>
                  )}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      statusStyles[version.status] || "bg-zinc-100 text-zinc-600"
                    }`}
                  >
                    {version.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-zinc-700">
                  {version.row_count.toLocaleString()}
                </td>
                <td className="px-4 py-2 text-zinc-700">
                  {version.column_count}
                </td>
                <td className="px-4 py-2">
                  {version.cleaning_issues && version.cleaning_issues.length > 0 ? (
                    <span className="font-medium text-amber-600">
                      {version.cleaning_issues.length}
                    </span>
                  ) : (
                    <span className="text-zinc-400">0</span>
                  )}
                </td>
                <td className="px-4 py-2 text-zinc-700">
                  {new Date(version.created_at).toLocaleString()}
                </td>
                {onDeleteVersion && (
                  <td className="px-4 py-2 text-right">
                    {!isActive ? (
                      <button
                        type="button"
                        onClick={() => onDeleteVersion(version)}
                        disabled={deletingVersionId === version.id}
                        className="rounded-md border border-rose-200 px-3 py-1 text-xs font-medium text-rose-700 transition hover:bg-rose-50 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {deletingVersionId === version.id ? "Deleting..." : "Delete Version"}
                      </button>
                    ) : (
                      <span className="text-xs text-zinc-400">Locked</span>
                    )}
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>

      {/* Show failed version details below the table */}
      {versions.filter(v => v.status === "failed" && v.failure_reason).length > 0 && (
        <div className="mt-4 space-y-2">
          <h4 className="text-sm font-semibold text-zinc-700">Failed Versions</h4>
          {versions.filter(v => v.status === "failed" && v.failure_reason).map(v => (
            <div key={v.id} className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              <span className="font-medium">v{v.version_number}:</span> {v.failure_reason}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
