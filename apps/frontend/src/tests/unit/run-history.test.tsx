import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("next/navigation", () => ({
  default: {},
  useRouter: () => ({ push: vi.fn() }),
}));

import { RunHistory } from "@/components/run-history";
import type { Run } from "@/lib/api/types";

const mockRuns: Run[] = [
  {
    id: "run-1",
    project_id: "p1",
    connection_id: "c1",
    dataset_id: "ds-1",
    status: "completed",
    started_by: "user-1",
    started_at: "2026-05-18T10:00:00Z",
    finished_at: "2026-05-18T10:05:30Z",
    duration_ms: 330000,
    warning_count: 0,
    error_message: null,
    created_at: "2026-05-18T09:55:00Z",
  },
  {
    id: "run-2",
    project_id: "p1",
    connection_id: "c1",
    dataset_id: "ds-1",
    status: "failed",
    started_by: "user-1",
    started_at: "2026-05-18T11:00:00Z",
    finished_at: null,
    duration_ms: null,
    warning_count: 3,
    error_message: "Timeout",
    created_at: "2026-05-18T10:55:00Z",
  },
];

describe("RunHistory", () => {
  it("renders empty state when runs is empty", () => {
    render(<RunHistory runs={[]} />);
    expect(screen.getByText("No runs yet")).toBeInTheDocument();
  });

  it("renders empty state when runs is undefined", () => {
    render(<RunHistory runs={undefined as unknown as []} />);
    expect(screen.getByText("No runs yet")).toBeInTheDocument();
  });

  it("renders table with run statuses", () => {
    render(<RunHistory runs={mockRuns} />);
    expect(screen.getByText("completed")).toBeInTheDocument();
    expect(screen.getByText("failed")).toBeInTheDocument();
  });

  it("displays formatted duration for completed runs", () => {
    render(<RunHistory runs={[mockRuns[0]]} />);
    expect(screen.getByText("5m 30s")).toBeInTheDocument();
  });

  it("displays '--' for runs with null duration", () => {
    render(<RunHistory runs={[mockRuns[1]]} />);
    expect(screen.getByText("--")).toBeInTheDocument();
  });

  it("shows warning count in amber when > 0", () => {
    render(<RunHistory runs={[mockRuns[1]]} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows 0 for warning count when none", () => {
    render(<RunHistory runs={[mockRuns[0]]} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("renders View link for each run", () => {
    render(<RunHistory runs={mockRuns} />);
    const links = screen.getAllByText("View");
    expect(links).toHaveLength(2);
  });

  it("displays 'Not started' when started_at is null", () => {
    const runWithNoStart: Run = {
      ...mockRuns[0],
      started_at: null,
    };
    render(<RunHistory runs={[runWithNoStart]} />);
    expect(screen.getByText("Not started")).toBeInTheDocument();
  });
});
