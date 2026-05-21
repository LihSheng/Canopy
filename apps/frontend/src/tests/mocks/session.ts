import { vi } from "vitest";

interface SessionMock {
  user: { id: string; email: string; display_name: string } | null;
  loading: boolean;
  error: string | null;
  refetch: (...args: any[]) => any;
  logout: (...args: any[]) => any;
}

export const createSessionMock = (overrides?: Partial<SessionMock>): SessionMock => ({
  user: { id: "1", email: "test@test.com", display_name: "Test User" },
  loading: false,
  error: null,
  refetch: vi.fn(),
  logout: vi.fn(),
  ...overrides,
});
