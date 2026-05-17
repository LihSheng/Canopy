"use client";

type Props = {
  columns: string[];
  rows: (string | null)[][];
  totalRowCount: number;
};

export function PreviewGrid({ columns = [], rows = [], totalRowCount = 0 }: Props) {
  if (!columns || columns.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-zinc-500">
        No data to display
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-zinc-200">
      <table className="min-w-full divide-y divide-zinc-200 text-sm">
        <thead>
          <tr className="bg-zinc-50">
            <th className="sticky left-0 bg-zinc-50 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500">
              #
            </th>
            {columns.map((col) => (
              <th
                key={col}
                className="whitespace-nowrap px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-zinc-500"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {rows.map((row, ri) => (
            <tr key={ri} className="hover:bg-zinc-50">
              <td className="sticky left-0 bg-white px-3 py-1.5 text-xs text-zinc-400">
                {ri + 1}
              </td>
              {row.map((cell, ci) => (
                <td
                  key={ci}
                  className="max-w-[300px] truncate whitespace-nowrap px-3 py-1.5 text-zinc-700"
                >
                  {cell ?? <span className="text-zinc-300">NULL</span>}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="border-t border-zinc-100 px-3 py-2 text-xs text-zinc-500">
        Showing {rows.length} of {totalRowCount} rows
      </div>
    </div>
  );
}
