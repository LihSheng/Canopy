"use client";

type StepState = "completed" | "current" | "pending" | "failed";

interface Step {
  label: string;
  state: StepState;
  onClick?: () => void;
}

interface WorkflowStepperProps {
  steps: Step[];
}

function StepIcon({ state }: { state: StepState }) {
  if (state === "completed") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-zinc-900 text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
          <path
            fillRule="evenodd"
            d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  }

  if (state === "current") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-zinc-900 bg-white">
        <span className="h-3 w-3 rounded-full bg-zinc-900" />
      </span>
    );
  }

  if (state === "failed") {
    return (
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-600 text-white">
        <svg viewBox="0 0 20 20" fill="currentColor" className="h-5 w-5">
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
            clipRule="evenodd"
          />
        </svg>
      </span>
    );
  }

  return (
    <span className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-zinc-300 bg-white">
      <span className="h-2 w-2 rounded-full bg-zinc-300" />
    </span>
  );
}

export function WorkflowStepper({ steps }: WorkflowStepperProps) {
  return (
    <div className="flex items-center justify-center py-4">
      {steps.map((step, i) => (
        <div key={step.label} className="flex items-center">
          {i > 0 && (
            <div
              className={`mx-1 h-0.5 w-8 sm:mx-2 sm:w-16 ${
                step.state === "pending"
                  ? "bg-zinc-200"
                  : step.state === "failed"
                    ? "bg-red-200"
                    : "bg-zinc-900"
              }`}
            />
          )}
          <button
            type="button"
            onClick={step.onClick}
            disabled={!step.onClick}
            className={`flex flex-col items-center gap-1 ${
              !step.onClick ? "cursor-default" : "cursor-pointer"
            }`}
            aria-label={`${step.label} - ${step.state}`}
          >
            <StepIcon state={step.state} />
            <span
              className={`text-xs font-medium ${
                step.state === "completed" || step.state === "current"
                  ? "text-zinc-900"
                  : step.state === "failed"
                    ? "text-red-600"
                    : "text-zinc-400"
              }`}
            >
              {step.label}
            </span>
          </button>
        </div>
      ))}
    </div>
  );
}

export function buildWorkflowSteps(
  status: string | null,
  onNavigate?: (step: string) => void,
): Step[] {
  const allSteps = ["Upload", "Profile", "Map", "Process", "Publish"];
  const stepKeys = ["upload", "profile", "mapping", "processing", "publish"];

  const statusOrder: Record<string, number> = {
    started: 0,
    profiled: 1,
    mapped: 2,
    processing: 3,
    processed: 4,
    published: 5,
    failed: -1,
  };

  const currentIdx = status ? statusOrder[status] ?? -1 : -1;

  return allSteps.map((label, i) => {
    const key = stepKeys[i];

    if (status === "failed") {
      return {
        label,
        state: "pending" as StepState,
        onClick: undefined,
      };
    }

    if (i < currentIdx) {
      return {
        label,
        state: "completed" as StepState,
        onClick: onNavigate ? () => onNavigate(key) : undefined,
      };
    }

    if (i === currentIdx) {
      return {
        label,
        state: "current" as StepState,
        onClick: undefined,
      };
    }

    return {
      label,
      state: "pending" as StepState,
      onClick: undefined,
    };
  });
}
