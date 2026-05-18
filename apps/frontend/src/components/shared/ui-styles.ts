export type NoticeTone = "info" | "warning" | "danger" | "success";
export type ButtonTone = "primary" | "secondary" | "danger" | "warning";

export const noticeToneStyles: Record<NoticeTone, string> = {
  info: "border-blue-200 bg-blue-50 text-blue-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  danger: "border-rose-200 bg-rose-50 text-rose-900",
  success: "border-emerald-200 bg-emerald-50 text-emerald-900",
};

export const buttonToneStyles: Record<ButtonTone, string> = {
  primary: "border-zinc-900 bg-zinc-900 text-white hover:bg-zinc-800",
  secondary: "border-zinc-200 bg-white text-zinc-700 hover:bg-zinc-50",
  danger: "border-rose-200 bg-rose-600 text-white hover:bg-rose-700",
  warning: "border-amber-200 bg-amber-600 text-white hover:bg-amber-700",
};

export const sharedButtonBase =
  "rounded-md border px-4 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
