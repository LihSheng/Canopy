import { describe, expect, it } from "vitest";
import { parseTimeRange, DEFAULT_TIME_RANGE, TIME_RANGE_LABELS } from "@/lib/navigation/time-range";

describe("TimeRangeKey", () => {
  it("has correct labels", () => {
    expect(TIME_RANGE_LABELS.this_month).toBe("This month");
    expect(TIME_RANGE_LABELS.last_3_months).toBe("Last 3 months");
    expect(TIME_RANGE_LABELS.last_12_months).toBe("Last 12 months");
  });

  describe("parseTimeRange", () => {
    it("returns default for null", () => {
      expect(parseTimeRange(null)).toBe(DEFAULT_TIME_RANGE);
    });

    it("returns default for undefined", () => {
      expect(parseTimeRange(undefined)).toBe(DEFAULT_TIME_RANGE);
    });

    it("returns default for unknown value", () => {
      expect(parseTimeRange("garbage")).toBe(DEFAULT_TIME_RANGE);
    });

    it("returns default for empty string", () => {
      expect(parseTimeRange("")).toBe(DEFAULT_TIME_RANGE);
    });

    it("parses last_3_months", () => {
      expect(parseTimeRange("last_3_months")).toBe("last_3_months");
    });

    it("parses last_12_months", () => {
      expect(parseTimeRange("last_12_months")).toBe("last_12_months");
    });

    it("parses this_month (default)", () => {
      expect(parseTimeRange("this_month")).toBe("this_month");
    });
  });
});
