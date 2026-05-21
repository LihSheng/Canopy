import { vi } from "vitest";

export interface RouterMockOverrides {
  push?: ReturnType<typeof vi.fn>;
  replace?: ReturnType<typeof vi.fn>;
  pathname?: string;
}

export const createRouterMock = (overrides?: RouterMockOverrides) => ({
  useRouter: () => ({
    push: overrides?.push ?? vi.fn(),
    replace: overrides?.replace ?? vi.fn(),
  }),
  usePathname: () => overrides?.pathname ?? "/dashboard",
  useSearchParams: () => new URLSearchParams(),
});
