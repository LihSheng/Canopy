import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";

type Props = {
  columns: string[];
  rows: (string | number | boolean | null)[][];
  loading: boolean;
  error: string | null;
};

function isNumeric(value: string | number | boolean | null): boolean {
  if (value === null) return false;
  if (typeof value === "boolean") return false;
  if (typeof value === "number") return true;
  const trimmed = value.trim();
  if (trimmed === "") return false;
  return !isNaN(Number(trimmed));
}

function inferColumnTypes(columns: string[], rows: (string | number | boolean | null)[][]): { numeric: number; text: number } {
  const sampleRows = rows.slice(0, 20);
  let numericCount = 0;
  let textCount = 0;

  for (let colIdx = 0; colIdx < columns.length; colIdx++) {
    const values = sampleRows.map((row) => row[colIdx]).filter((v) => v !== null && v !== "");
    if (values.length === 0) {
      textCount++;
      continue;
    }
    const numericValues = values.filter(isNumeric);
    if (numericValues.length > values.length / 2) {
      numericCount++;
    } else {
      textCount++;
    }
  }

  return { numeric: numericCount, text: textCount };
}

export function DatasetCharts({ columns, rows, loading, error }: Props) {
  if (loading) {
    return <LoadingSpinner text="Loading charts..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!columns || columns.length === 0) {
    return <EmptyState title="No data" description="No columns to chart." />;
  }

  const { numeric, text } = inferColumnTypes(columns, rows);
  const total = numeric + text;
  const numericPct = total > 0 ? Math.round((numeric / total) * 100) : 0;
  const textPct = 100 - numericPct;

  return (
    <div className="space-y-6">
      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <h3 className="mb-4 text-sm font-semibold text-zinc-900">Column Type Distribution</h3>
        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Numeric</span>
              <span>{numeric} ({numericPct}%)</span>
            </div>
            <div className="mt-1 h-4 w-full overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-blue-500 transition-all"
                style={{ width: `${numericPct}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Text</span>
              <span>{text} ({textPct}%)</span>
            </div>
            <div className="mt-1 h-4 w-full overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-emerald-500 transition-all"
                style={{ width: `${textPct}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-zinc-200 bg-white p-4">
        <h3 className="mb-1 text-sm font-semibold text-zinc-900">Row Count</h3>
        <p className="text-2xl font-semibold text-zinc-900">{rows.length.toLocaleString()}</p>
        <p className="text-xs text-zinc-500">rows in current preview window</p>
      </div>
    </div>
  );
}
