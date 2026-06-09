"use client";

import React, { useState, useEffect } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { aggregateObjectSet, AggregationBucket, AggregationType } from "@/lib/api/semantic";
import type { PropertyMapping } from "@/lib/api/types";
import { LoadingSpinner } from "@/components/shared/loading-spinner";

type BarClickEvent = {
  activePayload?: Array<{ payload: AggregationBucket }>;
};

interface WorkshopChartXYProps {
  objectTypeId: string;
  mappingProperties: PropertyMapping[];
  onSelectionChange?: (filterValue: string | null, dimensionName?: string) => void;
  selectedValue?: string | null;
}

export const WorkshopChartXY = ({
  objectTypeId,
  mappingProperties,
  onSelectionChange,
  selectedValue,
}: WorkshopChartXYProps) => {
  const includedProperties = mappingProperties.filter((p) => p.included);

  const [dimension, setDimension] = useState<string>(
    includedProperties[0]?.property_name || ""
  );
  const [metricProp, setMetricProp] = useState<string>(
    includedProperties[0]?.property_name || ""
  );
  const [aggType, setAggType] = useState<AggregationType>("count");
  const [data, setData] = useState<AggregationBucket[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch aggregated data
  useEffect(() => {
    if (!objectTypeId || !dimension || !metricProp) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    aggregateObjectSet(objectTypeId, {
      object_type_id: objectTypeId,
      dimension,
      metric: {
        property: metricProp,
        type: aggType,
      },
    })
      .then((res) => {
        if (isMounted) {
          setData(res.results || []);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || "Failed to load visualization data");
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [objectTypeId, dimension, metricProp, aggType]);

  const selectedMetricProperty = includedProperties.find(
    (p) => p.property_name === metricProp
  );
  const isMetricNumeric =
    selectedMetricProperty &&
    ["integer", "number"].includes(selectedMetricProperty.semantic_type);

  // If metric property changes to non-numeric, reset aggregation to 'count' if it was a numeric aggregation
  useEffect(() => {
    if (!isMetricNumeric && ["sum", "avg", "min", "max"].includes(aggType)) {
      setAggType("count");
    }
  }, [metricProp, isMetricNumeric, aggType]);

  const handleBarClick = (entry: AggregationBucket) => {
    if (!onSelectionChange) return;

    const clickedValue = entry?.dimension_value;
    if (clickedValue === undefined) return;

    if (selectedValue === clickedValue) {
      onSelectionChange(null, dimension);
    } else {
      onSelectionChange(clickedValue, dimension);
    }
  };

  if (includedProperties.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-6">
        <p className="text-sm text-zinc-400">No properties available for charting.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-zinc-100 pb-4 mb-4">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
          Entity Aggregation Chart
        </h3>
        
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <label htmlFor="xAxis-select" className="text-xs font-medium text-zinc-500">
              X-Axis
            </label>
            <select
              id="xAxis-select"
              name="xAxis"
              value={dimension}
              onChange={(e) => setDimension(e.target.value)}
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {includedProperties.map((p) => (
                <option key={p.source_column} value={p.property_name}>
                  {p.property_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="metric-select" className="text-xs font-medium text-zinc-500">
              Metric
            </label>
            <select
              id="metric-select"
              name="metric"
              value={metricProp}
              onChange={(e) => setMetricProp(e.target.value)}
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {includedProperties.map((p) => (
                <option key={p.source_column} value={p.property_name}>
                  {p.property_name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="agg-select" className="text-xs font-medium text-zinc-500">
              Aggregation
            </label>
            <select
              id="agg-select"
              name="aggregation"
              value={aggType}
              onChange={(e) => setAggType(e.target.value as AggregationType)}
              className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-xs text-zinc-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="count">Count</option>
              <option value="count_distinct">Count Distinct</option>
              <option value="sum" disabled={!isMetricNumeric}>
                Sum
              </option>
              <option value="avg" disabled={!isMetricNumeric}>
                Average
              </option>
              <option value="min" disabled={!isMetricNumeric}>
                Minimum
              </option>
              <option value="max" disabled={!isMetricNumeric}>
                Maximum
              </option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <ChartSkeleton />
      ) : error ? (
        <div className="flex h-64 items-center justify-center">
          <p className="text-sm text-red-500">{error}</p>
        </div>
      ) : data.length === 0 ? (
        <div className="flex h-64 items-center justify-center">
          <p className="text-sm text-zinc-400">No data found</p>
        </div>
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={data}
              onClick={(state: BarClickEvent) => {
                if (state && state.activePayload && state.activePayload.length > 0) {
                  handleBarClick(state.activePayload[0].payload);
                }
              }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis
                dataKey="dimension_value"
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={{ stroke: "#e5e7eb" }}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e5e7eb",
                  boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="metric_value" radius={[4, 4, 0, 0]}>
                {data.map((entry, index) => {
                  const isSelected = selectedValue === entry.dimension_value;
                  return (
                    <Cell
                      key={`cell-${index}`}
                      fill={isSelected ? "#111111" : "#3b82f6"}
                      className="cursor-pointer hover:opacity-80 transition-opacity"
                    />
                  );
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

const ChartSkeleton = () => {
  return (
    <div className="flex h-72 items-center justify-center">
      <LoadingSpinner text="Loading visualization data..." />
    </div>
  );
};
