import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SyncPolicyEditor, type SyncPolicy } from "@/components/data-studio/sync-policy-editor";

const BASE_POLICY: SyncPolicy = {
  syncMode: "batch",
  batchStrategy: "full_snapshot",
  cursorColumn: "updated_at",
  frequencyMinutes: 60,
};

const SCHEMA_COLUMNS = [
  { name: "id", data_type: "bigint" },
  { name: "updated_at", data_type: "timestamp" },
  { name: "created_at", data_type: "timestamp" },
];

describe("SyncPolicyEditor", () => {
  it("renders table name", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={BASE_POLICY}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("users")).toBeInTheDocument();
  });

  it("shows auto-detected badge when detectedCursorColumn is set", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={BASE_POLICY}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("auto-detected")).toBeInTheDocument();
  });

  it("shows manual badge when no detection but timestamp columns exist", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn={null}
        value={{ ...BASE_POLICY, cursorColumn: "created_at" }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("manual")).toBeInTheDocument();
  });

  it("shows warning when no cursor column can be detected", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={[{ name: "id", data_type: "bigint" }]}
        detectedCursorColumn={null}
        value={BASE_POLICY}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText(/No timestamp columns found/)).toBeInTheDocument();
  });

  it("calls onChange when sync mode changes", () => {
    const onChange = vi.fn();
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={BASE_POLICY}
        onChange={onChange}
      />,
    );
    fireEvent.click(screen.getByText("Real-Time"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ syncMode: "real_time" }),
    );
  });

  it("shows batch-specific settings when sync mode is batch", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={BASE_POLICY}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByText("Strategy")).toBeInTheDocument();
    expect(screen.getByText("Frequency")).toBeInTheDocument();
    expect(screen.getByText("Full Snapshot")).toBeInTheDocument();
    expect(screen.getByText("Incremental Cursor")).toBeInTheDocument();
  });
});
