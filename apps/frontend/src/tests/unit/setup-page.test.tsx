import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mockSearchParams = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useSearchParams: () => mockSearchParams(),
}));

vi.mock("@/lib/api/data-source", () => ({
  previewStaticFile: vi.fn(),
  createConnection: vi.fn(),
  fetchConnectionTest: vi.fn(),
  fetchTableDiscovery: vi.fn(),
  createDataset: vi.fn(),
  fetchProjects: vi.fn().mockResolvedValue([]),
  createProject: vi.fn(),
  deleteStaticFilePreview: vi.fn(),
}));

vi.mock("next/link", () => ({
  default: ({ href, children, ...props }: { href: string; children: React.ReactNode }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

import SetupPage from "@/app/dashboard/connections/setup/page";

describe("SetupPage - Database source", () => {
  it("renders connection form for postgresql source", () => {
    mockSearchParams.mockReturnValue(new URLSearchParams("source=postgresql"));
    render(<SetupPage />);

    expect(screen.getByText("Connect Database")).toBeInTheDocument();
    expect(screen.getByText("Host")).toBeInTheDocument();
    expect(screen.getByText("Port")).toBeInTheDocument();
    expect(screen.getByText("Database")).toBeInTheDocument();
    expect(screen.getByText("Username")).toBeInTheDocument();
    expect(screen.getByText("Password")).toBeInTheDocument();
    expect(screen.getByText("Test Connection")).toBeInTheDocument();
  });
});

describe("SetupPage - Static file source", () => {
  it("renders file upload for static_file source", () => {
    mockSearchParams.mockReturnValue(new URLSearchParams("source=static_file"));
    render(<SetupPage />);

    expect(screen.getByText("Upload File")).toBeInTheDocument();
    expect(screen.getByText(/Drop your file here/i)).toBeInTheDocument();
  });
});
