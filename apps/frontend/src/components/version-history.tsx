import type { DatasetVersion } from "@/lib/api/types";

type Props = {
  versions: DatasetVersion[];
  activeVersionId: string | null | undefined;
};

const statusStyles: Record<string, string> = {
  ready: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  pending: "bg-amber-100 text-amber-800",
  processing: "bg-blue-100 text-blue-800",
};

export function VersionHistory({ versions = [], activeVersionId }: Props) {
  if (!versions || versions.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No versions yet
      </div>
    );
  }

  return (
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
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {versions.map((version) => {
            const isActive = version.id === activeVersionId;
            return (
              <tr key={version.id} className="hover:bg-zinc-50">
                <td className="px-4 py-2">
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                      isActive
                        ? "bg-zinc-900 text-white"
                        : "bg-zinc-100 text-zinc-700"
                    }`}
                  >
                    v{version.version_number}
                  </span>
                  {isActive && (
                    <span className="ml-2 text-xs font-medium text-zinc-500">Active</span>
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
