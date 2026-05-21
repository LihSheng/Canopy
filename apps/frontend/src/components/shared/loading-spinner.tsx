import { UI_LABELS } from "@/lib/constants";

export function LoadingSpinner({ text = UI_LABELS.loading }: { text?: string }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-4 rounded-2xl border border-zinc-200 bg-white py-10 text-center shadow-sm"
      role="status"
    >
      <div className="rounded-full border border-zinc-200 bg-zinc-50 p-3">
        <svg
          className="h-6 w-6 animate-spin text-zinc-500"
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
      </div>
      <p className="text-sm font-medium text-zinc-700">{text}</p>
    </div>
  );
}
