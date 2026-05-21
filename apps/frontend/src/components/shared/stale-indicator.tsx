import { NoticeBanner } from "./notice-banner";

export const StaleIndicator = ({ lastUpdated }: { lastUpdated?: string }) => {
  if (!lastUpdated) return null;

  return (
    <NoticeBanner
      tone="info"
      title="Data freshness"
      description={`Data as of ${new Date(lastUpdated).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })}`}
    />
  );
}
