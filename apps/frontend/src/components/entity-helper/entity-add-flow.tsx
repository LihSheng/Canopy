"use client";

import { useState } from "react";
import { EntityAddEntryModal } from "./entity-add-entry-modal";
import { CreateNewEntityFlow } from "./create-new-entity-flow";
import { AttachExistingEntityFlow } from "./attach-existing-entity-flow";

interface EntityAddFlowProps {
  /** Optional: pre-selected dataset ID to attach (from Data Studio entrypoint) */
  datasetId?: string;
}

/**
 * Main orchestrator for the Entity Add Flow.
 *
 * Manages the entry modal and the two flow branches:
 * - Create New Entity (Palantir-style helper)
 * - Attach Existing Entity (search-and-fork)
 */
export function EntityAddFlow({ datasetId }: EntityAddFlowProps) {
  const [showModal, setShowModal] = useState(false);
  const [mode, setMode] = useState<"create" | "attach" | null>(null);

  const handleOpen = () => setShowModal(true);
  const handleClose = () => {
    setShowModal(false);
    setMode(null);
  };

  const handleChooseCreateNew = () => {
    setMode("create");
  };

  const handleChooseAttachExisting = () => {
    setMode("attach");
  };

  return (
    <>
      {/* Trigger button */}
      <button
        type="button"
        onClick={handleOpen}
        className="shrink-0 rounded-md bg-zinc-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-zinc-800"
      >
        <span className="flex items-center gap-1.5">
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          Add Entity
        </span>
      </button>

      {/* Entry modal */}
      <EntityAddEntryModal
        open={showModal && mode === null}
        onClose={handleClose}
        onChooseCreateNew={handleChooseCreateNew}
        onChooseAttachExisting={handleChooseAttachExisting}
      />

      {/* Create-New flow */}
      {mode === "create" && (
        <CreateNewEntityFlow onClose={handleClose} />
      )}

      {/* Attach-Existing flow */}
      {mode === "attach" && (
        <AttachExistingEntityFlow
          onClose={handleClose}
          datasetId={datasetId}
        />
      )}
    </>
  );
}
