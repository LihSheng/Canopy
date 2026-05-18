import { NoticeBanner } from "./notice-banner";

export function EmptyState({
  title = "No data available",
  description,
}: {
  title?: string;
  description?: string;
}) {
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
