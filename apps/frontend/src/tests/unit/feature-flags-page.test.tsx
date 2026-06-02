import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { FeatureFlagsPage } from "@/components/admin/feature-flags-page";
import type { FeatureFlag } from "@/lib/api/feature-flags";

// Mock feature flags API
const mockFetchAllFlags = vi.fn();
const mockToggleFlag = vi.fn();
vi.mock("@/lib/api/feature-flags", () => ({
  fetchAllFlags: (...args: unknown[]) => mockFetchAllFlags(...args),
  toggleFlag: (...args: unknown[]) => mockToggleFlag(...args),
}));

// Mock context refresh
const mockRefresh = vi.fn();
vi.mock("@/lib/feature-flags-context", () => ({
  useFeatureFlags: () => ({
    flags: { entity_canvas_enabled: true },
    loading: false,
    error: null,
    refresh: mockRefresh,
  }),
}));

// Mock shared components
vi.mock("@/components/shared", async () => {
  const actual = await vi.importActual("@/components/shared");
  return { ...actual };
});

// ─── Fixtures ───

const mockFlags: FeatureFlag[] = [
  {
    flag_key: "entity_canvas_enabled",
    description: "Enable the Entity Designer Graph Canvas.",
    enabled: true,
  },
  {
    flag_key: "dark_mode",
    description: "Enable dark mode for the UI.",
    enabled: false,
  },
];

// ─── Tests ───

describe("FeatureFlagsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading spinner while fetching flags", async () => {
    mockFetchAllFlags.mockReturnValue(new Promise(() => {})); // never resolves
    render(<FeatureFlagsPage />);
    expect(screen.getByText("Loading feature flags...")).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    mockFetchAllFlags.mockRejectedValue(new Error("Network error"));
    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("shows feature flags with toggle switches", async () => {
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("entity_canvas_enabled")
      ).toBeInTheDocument();
      expect(screen.getByText("dark_mode")).toBeInTheDocument();
    });

    // Descriptions are visible
    expect(
      screen.getByText("Enable the Entity Designer Graph Canvas.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Enable dark mode for the UI.")
    ).toBeInTheDocument();
  });

  it("shows empty state when no flags exist", async () => {
    mockFetchAllFlags.mockResolvedValue([]);
    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("No feature flags configured.")
      ).toBeInTheDocument();
    });
  });

  it("toggles a flag from on to off", async () => {
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    mockToggleFlag.mockResolvedValue({
      flag_key: "entity_canvas_enabled",
      description: "Enable the Entity Designer Graph Canvas.",
      enabled: false,
    });

    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("entity_canvas_enabled")
      ).toBeInTheDocument();
    });

    // Find the toggle for entity_canvas_enabled
    const toggle = screen.getByRole("switch", {
      name: "Toggle entity_canvas_enabled",
    });
    expect(toggle).toHaveAttribute("aria-checked", "true");

    fireEvent.click(toggle);

    await waitFor(() => {
      expect(mockToggleFlag).toHaveBeenCalledWith(
        "entity_canvas_enabled",
        false
      );
    });

    // Context refresh is called after toggle
    expect(mockRefresh).toHaveBeenCalled();
  });

  it("toggles a flag from off to on", async () => {
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    mockToggleFlag.mockResolvedValue({
      flag_key: "dark_mode",
      description: "Enable dark mode for the UI.",
      enabled: true,
    });

    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(screen.getByText("dark_mode")).toBeInTheDocument();
    });

    const toggle = screen.getByRole("switch", { name: "Toggle dark_mode" });
    expect(toggle).toHaveAttribute("aria-checked", "false");

    fireEvent.click(toggle);

    await waitFor(() => {
      expect(mockToggleFlag).toHaveBeenCalledWith("dark_mode", true);
    });
  });

  it("disables toggle while request is in flight", async () => {
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    // never-resolving promise to keep toggling state active
    mockToggleFlag.mockReturnValue(new Promise(() => {}));

    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("entity_canvas_enabled")
      ).toBeInTheDocument();
    });

    const toggle = screen.getByRole("switch", {
      name: "Toggle entity_canvas_enabled",
    });
    fireEvent.click(toggle);

    // Toggle should be disabled while toggling
    expect(toggle).toBeDisabled();
  });

  it("shows error when toggle fails", async () => {
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    mockToggleFlag.mockRejectedValue(new Error("Server error"));

    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("entity_canvas_enabled")
      ).toBeInTheDocument();
    });

    const toggle = screen.getByRole("switch", {
      name: "Toggle entity_canvas_enabled",
    });
    fireEvent.click(toggle);

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });

  it("renders retry button on error state", async () => {
    mockFetchAllFlags.mockRejectedValue(new Error("Load error"));
    render(<FeatureFlagsPage />);

    await waitFor(() => {
      expect(screen.getByText("Load error")).toBeInTheDocument();
    });

    // Retry button should exist
    const retryBtn = screen.getByText("Try again");
    expect(retryBtn).toBeInTheDocument();

    // Clicking retry should call fetch again
    mockFetchAllFlags.mockResolvedValue(mockFlags);
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(
        screen.getByText("entity_canvas_enabled")
      ).toBeInTheDocument();
    });
  });
});
