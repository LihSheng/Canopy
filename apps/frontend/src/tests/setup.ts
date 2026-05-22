import "@testing-library/jest-dom/vitest";

// Polyfill for @glideapps/glide-data-grid which requires ResizeObserver
if (typeof ResizeObserver === "undefined") {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (globalThis as { ResizeObserver?: typeof ResizeObserverStub }).ResizeObserver =
    ResizeObserverStub as unknown as typeof ResizeObserver;
}
