import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WorkshopChartXY } from "@/components/data-studio/workshop/WorkshopChartXY";
import * as semanticApi from "@/lib/api/semantic";
import type { PropertyMapping } from "@/lib/api/types";

// Mock Recharts to render simple divs instead of complex SVG
vi.mock("recharts", () => {
  const MockContainer = ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  );
  const MockBarChart = ({
    children,
    data,
    onClick,
  }: {
    children?: React.ReactNode;
    data?: { dimension_value: string; metric_value: number }[];
    onClick?: (event: { activePayload?: { payload: { dimension_value: string; metric_value: number } }[] }) => void;
  }) => {
    const handleClick = () => {
      if (onClick && data && data.length > 0) {
        onClick({ activePayload: [{ payload: data[0] }] });
      }
    };
    return (
      <div data-testid="bar-chart" onClick={handleClick}>
        {data && data.map((item: { dimension_value: string; metric_value: number }, index: number) => (
          <div key={index} data-testid="bar-element">
            {item.dimension_value}: {item.metric_value}
          </div>
        ))}
        {children}
      </div>
    );
  };
  const MockBar = ({ children }: { children?: React.ReactNode }) => <div data-testid="bar">{children}</div>;
  return {
    ResponsiveContainer: MockContainer,
    BarChart: MockBarChart,
    Bar: MockBar,
    Cell: () => <div data-testid="cell" />,
    XAxis: () => <div data-testid="xaxis" />,
    YAxis: () => <div data-testid="yaxis" />,
    CartesianGrid: () => null,
    Tooltip: () => <div data-testid="tooltip" />,
  };
});

// Mock semantic API module
vi.mock("@/lib/api/semantic", () => ({
  aggregateObjectSet: vi.fn(),
}));

const mockProperties: PropertyMapping[] = [
  { source_column: "dept", property_name: "Department", semantic_type: "string", included: true, is_primary_key: false },
  { source_column: "salary", property_name: "Salary", semantic_type: "number", included: true, is_primary_key: false },
  { source_column: "age", property_name: "Age", semantic_type: "integer", included: true, is_primary_key: false },
  { source_column: "ignored", property_name: "Ignored", semantic_type: "string", included: false, is_primary_key: false },
];

describe("WorkshopChartXY", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders dropdown selectors and calls aggregateObjectSet on mount", async () => {
    const mockAggregate = vi.mocked(semanticApi.aggregateObjectSet).mockResolvedValue({
      object_type: "employee",
      results: [
        { dimension_value: "HR", metric_value: 10 },
        { dimension_value: "IT", metric_value: 25 },
      ],
      truncated: false,
    });

    render(
      <WorkshopChartXY
        objectTypeId="obj-1"
        mappingProperties={mockProperties}
      />
    );

    // Verify dropdowns exist
    expect(screen.getByLabelText("X-Axis")).toBeInTheDocument();
    expect(screen.getByLabelText("Metric")).toBeInTheDocument();
    expect(screen.getByLabelText("Aggregation")).toBeInTheDocument();

    // Verify loading API call is made with defaults:
    // X-Axis = Department (first mapping property), Aggregation = count
    await waitFor(() => {
      expect(mockAggregate).toHaveBeenCalledWith("obj-1", {
        object_type_id: "obj-1",
        dimension: "Department",
        metric: {
          property: "Department",
          type: "count",
        },
      });
    });

    // Check custom bar chart elements are rendered
    await waitFor(() => {
      expect(screen.getByText("HR: 10")).toBeInTheDocument();
      expect(screen.getByText("IT: 25")).toBeInTheDocument();
    });
  });

  it("calls aggregateObjectSet when dropdown selections change", async () => {
    const mockAggregate = vi.mocked(semanticApi.aggregateObjectSet).mockResolvedValue({
      object_type: "employee",
      results: [],
      truncated: false,
    });

    render(
      <WorkshopChartXY
        objectTypeId="obj-1"
        mappingProperties={mockProperties}
      />
    );

    await waitFor(() => {
      expect(mockAggregate).toHaveBeenCalledTimes(1);
    });

    // Change metric to Salary, aggregation to sum
    const metricSelect = screen.getByLabelText("Metric");
    fireEvent.change(metricSelect, { target: { value: "Salary" } });

    const aggSelect = screen.getByLabelText("Aggregation");
    fireEvent.change(aggSelect, { target: { value: "sum" } });

    await waitFor(() => {
      expect(mockAggregate).toHaveBeenLastCalledWith("obj-1", {
        object_type_id: "obj-1",
        dimension: "Department",
        metric: {
          property: "Salary",
          type: "sum",
        },
      });
    });
  });

  it("triggers onSelectionChange with dimension value when a bar is clicked", async () => {
    vi.mocked(semanticApi.aggregateObjectSet).mockResolvedValue({
      object_type: "employee",
      results: [
        { dimension_value: "HR", metric_value: 10 },
      ],
      truncated: false,
    });

    const mockSelectChange = vi.fn();

    render(
      <WorkshopChartXY
        objectTypeId="obj-1"
        mappingProperties={mockProperties}
        onSelectionChange={mockSelectChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("HR: 10")).toBeInTheDocument();
    });

    // Click bar-chart
    const chart = screen.getByTestId("bar-chart");
    fireEvent.click(chart);

    expect(mockSelectChange).toHaveBeenCalledWith("HR", "Department");
  });
});
