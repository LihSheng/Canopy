import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { LineageView } from "@/components/lineage-view";

describe("LineageView", () => {
  it("renders empty state when nodes is empty", () => {
    render(<LineageView nodes={[]} edges={[]} />);
    expect(screen.getByText("No lineage data available")).toBeInTheDocument();
  });

  it("renders empty state when nodes is undefined", () => {
    render(<LineageView nodes={undefined as unknown as []} edges={[]} />);
    expect(screen.getByText("No lineage data available")).toBeInTheDocument();
  });

  it("renders node labels and types", () => {
    const nodes = [
      { id: "1", type: "table", label: "users" },
      { id: "2", type: "table", label: "orders" },
    ];
    render(<LineageView nodes={nodes} edges={[]} />);

    expect(screen.getByText("users")).toBeInTheDocument();
    expect(screen.getByText("orders")).toBeInTheDocument();
    expect(screen.getAllByText("table")).toHaveLength(2);
  });

  it("renders edges section when edges exist", () => {
    const nodes = [
      { id: "1", type: "table", label: "users" },
      { id: "2", type: "table", label: "orders" },
    ];
    const edges = [
      { from: "1", to: "2", type: "fk" },
    ];
    render(<LineageView nodes={nodes} edges={edges} />);

    expect(screen.getByText("Edges")).toBeInTheDocument();
    expect(screen.getByText("users → orders")).toBeInTheDocument();
    expect(screen.getByText("(fk)")).toBeInTheDocument();
  });

  it("resolves node labels via nodeMap for edge display", () => {
    const nodes = [
      { id: "src", type: "file", label: "source.csv" },
      { id: "dest", type: "table", label: "imported" },
    ];
    const edges = [{ from: "src", to: "dest", type: "load" }];
    render(<LineageView nodes={nodes} edges={edges} />);

    expect(screen.getByText("source.csv → imported")).toBeInTheDocument();
  });

  it("shows empty state when nodes are empty even if edges exist", () => {
    const edges = [{ from: "unknown-1", to: "unknown-2", type: "ref" }];
    render(<LineageView nodes={[]} edges={edges} />);

    expect(screen.getByText("No lineage data available")).toBeInTheDocument();
    expect(screen.queryByText("Edges")).not.toBeInTheDocument();
  });

  it("does not render Edges section when edges array is empty", () => {
    render(<LineageView nodes={[{ id: "1", type: "table", label: "users" }]} edges={[]} />);
    expect(screen.queryByText("Edges")).not.toBeInTheDocument();
  });
});
