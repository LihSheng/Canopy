import { noticeToneStyles, type NoticeTone } from "./ui-styles";

type Props = {
  tone?: NoticeTone;
  title: string;
  description?: string;
  className?: string;
};

export function NoticeBanner({ tone = "info", title, description, className = "" }: Props) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${noticeToneStyles[tone]} ${className}`.trim()}>
      <p className="font-medium">{title}</p>
      {description && <p className="mt-1 text-sm opacity-90">{description}</p>}
    </div>
  );
}
