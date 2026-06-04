"use client";

import { useState } from "react";

interface EntityAddEntryModalProps {
  open: boolean;
  onClose: () => void;
  onChooseCreateNew: () => void;
  onChooseAttachExisting: () => void;
}

/**
 * Entry modal for the Entity Add Flow.
 *
 * User chooses between "Create New Entity" (Palantir-style helper)
 * and "Attach Existing Entity" (search-and-fork flow).
 */
export function EntityAddEntryModal({
  open,
  onClose,
  onChooseCreateNew,
  onChooseAttachExisting,
}: EntityAddEntryModalProps) {
  const [closing, setClosing] = useState(false);

  if (!open) return null;

  const handleClose = () => {
    setClosing(true);
    setTimeout(() => {
      setClosing(false);
      onClose();
    }, 150);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-label="Add Entity"
    >
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-zinc-900/40 transition-opacity duration-150 ${
          closing ? "opacity-0" : "opacity-100"
        }`}
        onClick={handleClose}
      />

      {/* Modal */}
      <div
        className={`relative z-10 w-full max-w-md rounded-xl bg-white shadow-xl ring-1 ring-zinc-200 transition-all duration-150 ${
          closing ? "opacity-0 scale-95" : "opacity-100 scale-100"
        }`}
      >
        {/* Header */}
        <div className="border-b border-zinc-100 px-6 py-4">
          <h2 className="text-base font-semibold text-zinc-900">Add Entity</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Choose how you want to add an entity to the registry.
          </p>
        </div>

        {/* Choice cards */}
        <div className="p-6 space-y-3">
          <button
            type="button"
            onClick={() => {
              handleClose();
              setTimeout(() => onChooseCreateNew(), 200);
            }}
            className="w-full rounded-lg border border-zinc-200 bg-white p-4 text-left transition-colors hover:border-zinc-300 hover:bg-zinc-50"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-100">
                <svg
                  className="h-4 w-4 text-zinc-600"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <div className="text-sm font-medium text-zinc-900">
                  Create New Entity
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Start a new business object with a guided helper. Optionally
                  choose a backing datasource, define properties, and build from
                  scratch.
                </div>
              </div>
            </div>
          </button>

          <button
            type="button"
            onClick={() => {
              handleClose();
              setTimeout(() => onChooseAttachExisting(), 200);
            }}
            className="w-full rounded-lg border border-zinc-200 bg-white p-4 text-left transition-colors hover:border-zinc-300 hover:bg-zinc-50"
          >
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-zinc-100">
                <svg
                  className="h-4 w-4 text-zinc-600"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div>
                <div className="text-sm font-medium text-zinc-900">
                  Attach Existing Entity
                </div>
                <div className="mt-0.5 text-xs text-zinc-500">
                  Search for an existing entity and attach a dataset to it. The
                  entity&apos;s schema stays as-is, with a new dataset linked
                  into it.
                </div>
              </div>
            </div>
          </button>
        </div>

        {/* Footer */}
        <div className="border-t border-zinc-100 px-6 py-3 flex justify-end">
          <button
            type="button"
            onClick={handleClose}
            className="rounded-md px-3 py-1.5 text-xs font-medium text-zinc-500 transition-colors hover:text-zinc-700"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
