import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CompactTable } from "@/components/shared/table/compact-table";
import type { ColumnDef } from "@/components/shared/table";

const columns: ColumnDef[] = [
  { key: "name", header: "Name" },
  {
    key: "status",
    header: "Status",
    render: (value) => (
      <span data-testid="status-badge">{String(value)}</span>
    ),
  },
  { key: "count", header: "Count", align: "right" },
];

const rows = [
  { id: "1", name: "Alice", status: "active", count: 5 },
  { id: "2", name: "Bob", status: "inactive", count: 10 },
];

describe("CompactTable", () => {
  it("renders headers and rows", () => {
    render(
      <CompactTable
        columns={columns}
        rows={rows as unknown as Record<string, unknown>[]}
        getRowId={(r) => String(r.id)}
      />
    );
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
  });

  it("renders custom cell content via render function", () => {
    render(
      <CompactTable
        columns={columns}
        rows={rows as unknown as Record<string, unknown>[]}
        getRowId={(r) => String(r.id)}
      />
    );
    const badges = screen.getAllByTestId("status-badge");
    expect(badges).toHaveLength(2);
    expect(badges[0]).toHaveTextContent("active");
  });

  it("shows loading spinner when loading", () => {
    render(
      <CompactTable
        columns={columns}
        rows={[]}
        getRowId={(r) => String(r.id)}
        loading
      />
    );
    expect(screen.getByText("Loading...")).toBeInTheDocument();
  });

  it("shows error state when error", () => {
    const onRetry = vi.fn();
    render(
      <CompactTable
        columns={columns}
        rows={[]}
        getRowId={(r) => String(r.id)}
        error="Something broke"
        onRetry={onRetry}
      />
    );
    expect(screen.getByText("Something broke")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Try again"));
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("shows empty state when no rows", () => {
    render(
      <CompactTable
        columns={columns}
        rows={[]}
        getRowId={(r) => String(r.id)}
        emptyText="Nothing here"
      />
    );
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("renders search input when onSearchChange is provided", () => {
    const onSearch = vi.fn();
    render(
      <CompactTable
        columns={columns}
        rows={rows as unknown as Record<string, unknown>[]}
        getRowId={(r) => String(r.id)}
        searchValue=""
        onSearchChange={onSearch}
        searchPlaceholder="Search..."
      />
    );
    const input = screen.getByPlaceholderText("Search...");
    expect(input).toBeInTheDocument();
    fireEvent.change(input, { target: { value: "test" } });
    expect(onSearch).toHaveBeenCalledWith("test");
  });

  it("renders pagination when page is provided", () => {
    const onPage = vi.fn();
    render(
      <CompactTable
        columns={columns}
        rows={rows as unknown as Record<string, unknown>[]}
        getRowId={(r) => String(r.id)}
        page={{ current: 1, total: 3 }}
        onPageChange={onPage}
      />
    );
    expect(screen.getByText("Page 1 of 3")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Next"));
    expect(onPage).toHaveBeenCalledWith(2);
  });
});
