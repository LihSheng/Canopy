"use client";

import type { ReactNode } from "react";

export interface HelperStep {
  key: string;
  label: string;
  /** Optional brief description shown under the step label */
  description?: string;
}

interface EntityHelperShellProps {
  /** Title shown at the top of the helper */
  title: string;
  /** Subtitle / context text */
  subtitle?: string;
  /** Ordered list of steps for the progress indicator */
  steps: HelperStep[];
  /** Currently active step index (0-based) */
  currentStep: number;
  /** Step content rendered in the main area */
  children: ReactNode;
  /** Whether back navigation is available */
  canGoBack: boolean;
  /** Whether forward/next is available */
  canGoNext: boolean;
  /** Label for the primary action button (defaults to "Next") */
  nextLabel?: string;
  /** Label for the back button (defaults to "Back") */
  backLabel?: string;
  /** Whether the primary action represents the final save (changes styling) */
  isLastStep?: boolean;
  /** Whether the helper is processing (disables buttons, shows spinner) */
  loading?: boolean;
  /** Error message to display */
  error?: string | null;
  onBack: () => void;
  onNext: () => void;
  onClose: () => void;
}

/**
 * Shared wizard shell for the Entity Add Flow.
 *
 * Used by both the Create-New and Attach-Existing flows.
 * Renders a step progress bar, step content area, and navigation buttons.
 */
export function EntityHelperShell({
  title,
  subtitle,
  steps,
  currentStep,
  children,
  canGoBack,
  canGoNext,
  nextLabel = "Next",
  backLabel = "Back",
  isLastStep = false,
  loading = false,
  error = null,
  onBack,
  onNext,
  onClose,
}: EntityHelperShellProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-zinc-900/40"
        onClick={onClose}
      />

      {/* Shell */}
      <div className="relative z-10 flex h-[min(85vh,680px)] w-full max-w-2xl flex-col rounded-xl bg-white shadow-xl ring-1 ring-zinc-200">
        {/* Header */}
        <div className="shrink-0 border-b border-zinc-100 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-zinc-900">{title}</h2>
              {subtitle && (
                <p className="mt-0.5 text-sm text-zinc-500">{subtitle}</p>
              )}
            </div>
            <button
              type="button"
              onClick={onClose}
              className="rounded-md p-1 text-zinc-400 transition-colors hover:text-zinc-600"
              aria-label="Close"
            >
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>

          {/* Step progress bar */}
          <div className="mt-4">
            <div className="flex items-center gap-1.5">
              {steps.map((step, i) => (
                <div key={step.key} className="flex items-center gap-1.5">
                  {/* Step dot */}
                  <button
                    type="button"
                    className={`flex h-6 min-w-0 items-center gap-1.5 rounded-full px-2.5 text-xs font-medium transition-colors ${
                      i === currentStep
                        ? "bg-zinc-900 text-white"
                        : i < currentStep
                          ? "bg-zinc-100 text-zinc-600"
                          : "bg-zinc-50 text-zinc-400"
                    }`}
                    title={step.description || step.label}
                    disabled
                  >
                    <span className="text-[10px] leading-none">{i + 1}</span>
                    <span className="hidden sm:inline">{step.label}</span>
                  </button>
                  {/* Connector line (except after last) */}
                  {i < steps.length - 1 && (
                    <div
                      className={`h-px w-4 ${
                        i < currentStep ? "bg-zinc-300" : "bg-zinc-200"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700">
              {error}
            </div>
          )}
          {children}
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-zinc-100 px-6 py-3 flex items-center justify-between">
          <button
            type="button"
            onClick={onBack}
            disabled={!canGoBack || loading}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
              canGoBack && !loading
                ? "text-zinc-600 hover:text-zinc-900"
                : "text-zinc-300"
            }`}
          >
            {backLabel}
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md px-3 py-1.5 text-xs font-medium text-zinc-400 transition-colors hover:text-zinc-600"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={onNext}
              disabled={!canGoNext || loading}
              className={`rounded-md px-4 py-1.5 text-xs font-medium transition-colors ${
                isLastStep
                  ? "bg-emerald-600 text-white hover:bg-emerald-700"
                  : "bg-zinc-900 text-white hover:bg-zinc-800"
              } disabled:opacity-40`}
            >
              {loading ? "Saving..." : nextLabel}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
