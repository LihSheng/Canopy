export function EmptyState({
  title = "No data available",
  description,
}: {
  title?: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      <p className="text-sm font-semibold text-zinc-900">{title}</p>
      {description && <p className="text-sm text-zinc-500">{description}</p>}
    </div>
  );
}
