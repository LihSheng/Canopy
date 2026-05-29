import { UI_LABELS } from "@/lib/constants";

export const LoadingSpinner = ({
  text = UI_LABELS.loading,
  className,
}: {
  text?: string;
  className?: string;
}) => {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 ${className ?? ""}`}
      role="status"
    >
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
      <p className="text-sm font-medium text-zinc-700">{text}</p>
    </div>
  );
};
