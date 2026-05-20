import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api/data-source", () => ({
  fetchSourceTypes: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import SourceCatalogContent from "@/app/dashboard/connections/sources/source-catalog-content";
import * as api from "@/lib/api/data-source";

describe("SourceCatalogContent", () => {
  it("renders source cards linking to setup page", async () => {
    vi.mocked(api.fetchSourceTypes).mockResolvedValue([
      {
        id: "postgresql",
        key: "postgresql",
        label: "PostgreSQL",
        description: "Connect to a Postgres database",
        enabled: true,
        tags: ["database", "relational"],
      },
      {
        id: "static_file",
        key: "static_file",
        label: "Static File",
        description: "Import from CSV or Excel",
        enabled: true,
        tags: ["file"],
      },
    ]);

    render(<SourceCatalogContent />);

    await waitFor(() => {
      expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    });

    // Each card should link directly to setup page with source param
    const pgLink = screen.getByText("PostgreSQL").closest("a");
    expect(pgLink).toHaveAttribute("href", "/dashboard/connections/setup?source=postgresql");

    const fileLink = screen.getByText("Static File").closest("a");
    expect(fileLink).toHaveAttribute("href", "/dashboard/connections/setup?source=static_file");
  });
});
