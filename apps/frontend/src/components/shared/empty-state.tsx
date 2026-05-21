import { NoticeBanner } from "./notice-banner";
import { UI_LABELS } from "@/lib/constants";

export function EmptyState({
  title = UI_LABELS.noData,
  description,
  variant = "default",
}: {
  title?: string;
  description?: string;
  variant?: "default" | "minimal";
}) {
  if (variant === "minimal") {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-base font-medium text-gray-900">{title}</p>
        {description && (
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        )}
      </div>
    );
  }

  return (
    <div className="py-12">
      <NoticeBanner
        tone="info"
        title={title}
        description={description}
        className="mx-auto max-w-md text-left"
      />
    </div>
  );
}
