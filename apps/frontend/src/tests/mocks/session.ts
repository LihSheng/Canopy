import { vi } from "vitest";

interface SessionMock {
  user: { id: string; email: string; display_name: string } | null;
  loading: boolean;
  error: string | null;
  refetch: (...args: unknown[]) => void;
  logout: (...args: unknown[]) => void;
}

export const createSessionMock = (overrides?: Partial<SessionMock>): SessionMock => ({
  user: { id: "1", email: "test@test.com", display_name: "Test User" },
  loading: false,
  error: null,
  refetch: vi.fn(),
  logout: vi.fn(),
  ...overrides,
});
