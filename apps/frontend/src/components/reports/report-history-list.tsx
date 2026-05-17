import type { ExportHistoryItem } from "./report-mappers";
import { ReportHistoryRow } from "./report-history-row";

export function ReportHistoryList({
  items,
  onRerun,
  exporting,
}: {
  items: ExportHistoryItem[];
  onRerun: (id: string) => void;
  exporting: string | null;
}) {
  if (items.length === 0) {
    return (
      <div>
        <h2 className="text-base font-semibold text-zinc-900 mb-4">Recent exports</h2>
        <p className="text-sm text-zinc-500">No recent exports. Generate one using the presets above.</p>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-base font-semibold text-zinc-900 mb-4">Recent exports</h2>
      <div className="space-y-3">
        {items.map((item) => (
          <ReportHistoryRow
            key={item.id}
            item={item}
            onRerun={onRerun}
            exporting={exporting}
          />
        ))}
      </div>
    </div>
  );
}
