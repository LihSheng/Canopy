import type { ExportPreset } from "./report-mappers";

export const ReportPresetGrid = ({
  presets,
  onTrigger,
  exporting,
}: {
  presets: ExportPreset[];
  onTrigger: (key: ExportPreset["key"]) => void;
  exporting: ExportPreset["key"] | null;
}) => {
  return (
    <div className="mb-8">
      <h2 className="text-base font-semibold text-zinc-900 mb-4">Export presets</h2>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {presets.map((preset) => {
          const busy = exporting === preset.key;
          return (
            <button
              key={preset.key}
              onClick={() => onTrigger(preset.key)}
              disabled={busy}
              className="flex flex-col items-start rounded-xl border border-zinc-200 bg-white p-4 text-left transition-colors hover:border-zinc-300 hover:bg-zinc-50 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <span className="text-sm font-semibold text-zinc-900">{preset.label}</span>
              <span className="mt-1 text-xs text-zinc-500">{preset.description}</span>
              {busy && (
                <span className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500">
                  <svg
                    className="h-3.5 w-3.5 animate-spin"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Generating...
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
