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
        value={{ ...BASE_POLICY, batchStrategy: "incremental_cursor" }}
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
        value={{ ...BASE_POLICY, batchStrategy: "incremental_cursor", cursorColumn: "created_at" }}
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
        value={{ ...BASE_POLICY, batchStrategy: "incremental_cursor" }}
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
        supportsCdc={true}
        sourceType="postgresql"
      />,
    );
    fireEvent.click(screen.getByText("Real-Time"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ syncMode: "real_time", realTimeStrategy: "cdc" }),
    );
  });

  it("defaults to polling for real-time mode when CDC is unsupported", () => {
    const onChange = vi.fn();
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={BASE_POLICY}
        onChange={onChange}
        supportsCdc={false}
        sourceType="postgresql"
      />,
    );
    fireEvent.click(screen.getByText("Real-Time"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ syncMode: "real_time", realTimeStrategy: "polling" }),
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
    expect(screen.getByText("Incremental Cursor")).toBeInTheDocument();
  });

  it("shows CDC warning and accelerated polling when supportsCdc is false and syncMode is real_time", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={{ ...BASE_POLICY, syncMode: "real_time" }}
        onChange={vi.fn()}
        supportsCdc={false}
        sourceType="postgresql"
      />,
    );
    expect(screen.getByText("CDC Stream Prerequisites Missing")).toBeInTheDocument();
    expect(screen.getByText(/wal_level = logical/)).toBeInTheDocument();
    expect(screen.getByText("Accelerated Polling")).toBeInTheDocument();
  });

  it("shows mysql CDC prerequisites when sourceType is mysql and supportsCdc is false", () => {
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={{ ...BASE_POLICY, syncMode: "real_time" }}
        onChange={vi.fn()}
        supportsCdc={false}
        sourceType="mysql"
      />,
    );
    expect(screen.getByText("CDC Stream Prerequisites Missing")).toBeInTheDocument();
    expect(screen.getByText(/log_bin = ON/)).toBeInTheDocument();
  });

  it("does not show CDC warning and allows CDC selection when supportsCdc is true", () => {
    const onChange = vi.fn();
    render(
      <SyncPolicyEditor
        tableName="users"
        schemaColumns={SCHEMA_COLUMNS}
        detectedCursorColumn="updated_at"
        value={{ ...BASE_POLICY, syncMode: "real_time", realTimeStrategy: "polling" }}
        onChange={onChange}
        supportsCdc={true}
        sourceType="postgresql"
      />,
    );
    expect(screen.queryByText("CDC Stream Prerequisites Missing")).not.toBeInTheDocument();
    
    // We can select "True CDC (Streaming)"
    fireEvent.click(screen.getByText("True CDC (Streaming)"));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ realTimeStrategy: "cdc" }),
    );
  });
});
