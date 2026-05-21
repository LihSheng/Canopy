import { vi } from "vitest";

export const createSessionMock = (overrides?: Partial<ReturnType<typeof createSessionMock>>) => ({
  user: { id: "1", email: "test@test.com", display_name: "Test User" },
  loading: false,
  error: null,
  refetch: vi.fn(),
  logout: vi.fn(),
  ...overrides,
});
