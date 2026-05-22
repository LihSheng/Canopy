import "@testing-library/jest-dom/vitest";

// Polyfill for @glideapps/glide-data-grid which requires ResizeObserver
if (typeof ResizeObserver === "undefined") {
  class ResizeObserverStub {
    constructor(_callback: ResizeObserverCallback) {}
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver;
}
