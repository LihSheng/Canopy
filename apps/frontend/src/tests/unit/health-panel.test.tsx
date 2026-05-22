import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { HealthPanel } from "@/components/health-panel";
import type { DatasetHealth } from "@/lib/api/types";

const baseHealth: DatasetHealth = {
  dataset_id: "ds-1",
  row_count: 15000,
  column_count: 8,
  missing_required_mappings: false,
  warning_count: 2,
  last_run_status: "completed",
  last_published_version: 3,
  freshness_at: "2026-05-18T10:00:00Z",
};

describe("HealthPanel", () => {
  it("renders all metric labels", () => {
    render(<HealthPanel health={baseHealth} />);

    expect(screen.getByText("Dataset Health")).toBeInTheDocument();
    expect(screen.getByText("Row Count")).toBeInTheDocument();
    expect(screen.getByText("Column Count")).toBeInTheDocument();
    expect(screen.getByText("Warnings")).toBeInTheDocument();
    expect(screen.getByText("Missing Mappings")).toBeInTheDocument();
    expect(screen.getByText("Last Run Status")).toBeInTheDocument();
    expect(screen.getByText("Last Published Version")).toBeInTheDocument();
    expect(screen.getByText("Freshness")).toBeInTheDocument();
  });

  it("formats row count with locale separator", () => {
    render(<HealthPanel health={baseHealth} />);
    expect(screen.getByText("15,000")).toBeInTheDocument();
  });

  it("displays column count", () => {
    render(<HealthPanel health={baseHealth} />);
    expect(screen.getByText("8")).toBeInTheDocument();
  });

  it("shows green 'No' for missing_required_mappings = false", () => {
    render(<HealthPanel health={baseHealth} />);
    const noElement = screen.getByText("No");
    expect(noElement.classList.contains("text-green-600")).toBe(true);
  });

  it("shows red 'Yes' for missing_required_mappings = true", () => {
    const health: DatasetHealth = { ...baseHealth, missing_required_mappings: true };
    render(<HealthPanel health={health} />);
    const yesElement = screen.getByText("Yes");
    expect(yesElement.classList.contains("text-red-600")).toBe(true);
  });

  it("renders last run status as a badge", () => {
    render(<HealthPanel health={baseHealth} />);
    expect(screen.getByText("completed")).toBeInTheDocument();
  });

  it("shows 'None' when last_run_status is null", () => {
    const health: DatasetHealth = { ...baseHealth, last_run_status: null };
    render(<HealthPanel health={health} />);
    expect(screen.getByText("None")).toBeInTheDocument();
  });

  it("shows last published version number", () => {
    render(<HealthPanel health={baseHealth} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("shows 'None' when last_published_version is null", () => {
    const health: DatasetHealth = { ...baseHealth, last_published_version: null };
    render(<HealthPanel health={health} />);
    expect(screen.getByText("None")).toBeInTheDocument();
  });

  it("formats freshness timestamp", () => {
    render(<HealthPanel health={baseHealth} />);
    expect(screen.getByText(/2026/)).toBeInTheDocument();
  });

  it("shows 'Unknown' when freshness_at is null", () => {
    const health: DatasetHealth = { ...baseHealth, freshness_at: null };
    render(<HealthPanel health={health} />);
    expect(screen.getByText("Unknown")).toBeInTheDocument();
  });
});
