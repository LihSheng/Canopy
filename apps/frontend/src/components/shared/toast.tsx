"use client";

import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { noticeToneStyles, type NoticeTone } from "./ui-styles";

type ToastItem = {
  id: string;
  tone: NoticeTone;
  title: string;
  description?: string;
};

type ToastInput = Omit<ToastItem, "id">;

type ToastContextValue = {
  showToast: (toast: ToastInput) => void;
  success: (title: string, description?: string) => void;
  info: (title: string, description?: string) => void;
  warning: (title: string, description?: string) => void;
  danger: (title: string, description?: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: string) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback((toast: ToastInput) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((current) => [...current, { ...toast, id }]);
    window.setTimeout(() => {
      dismissToast(id);
    }, 3500);
  }, [dismissToast]);

  const value = useMemo<ToastContextValue>(() => ({
    showToast,
    success: (title: string, description?: string) => showToast({ tone: "success", title, description }),
    info: (title: string, description?: string) => showToast({ tone: "info", title, description }),
    warning: (title: string, description?: string) => showToast({ tone: "warning", title, description }),
    danger: (title: string, description?: string) => showToast({ tone: "danger", title, description }),
  }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} onDismiss={dismissToast} />
    </ToastContext.Provider>
  );
}

export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}

const ToastViewport = ({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
}) => {
  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className="fixed right-4 top-4 z-50 flex w-full max-w-sm flex-col gap-3 px-4 sm:px-0">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={`rounded-xl border px-4 py-3 shadow-lg ${noticeToneStyles[toast.tone]}`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-sm font-semibold">{toast.title}</p>
              {toast.description && (
                <p className="mt-1 text-sm opacity-90">{toast.description}</p>
              )}
            </div>
            <button
              type="button"
              onClick={() => onDismiss(toast.id)}
              className="rounded-md px-2 py-1 text-xs font-medium opacity-70 transition hover:opacity-100"
              aria-label="Dismiss notification"
            >
              ×
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
