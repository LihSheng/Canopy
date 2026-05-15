export function StaleIndicator({ lastUpdated }: { lastUpdated?: string }) {
  if (!lastUpdated) return null;

  return (
    <p className="text-xs text-zinc-400">
      Data as of {new Date(lastUpdated).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}
    </p>
  );
}
