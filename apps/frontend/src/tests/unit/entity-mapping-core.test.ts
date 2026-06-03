import { describe, expect, it } from "vitest";
import {
  buildInitialPropertiesFromSchema,
  buildMappingRequest,
} from "@/components/entity-mapping/entity-mapping-core";

describe("entity-mapping-core", () => {
  it("builds the same mapping defaults for wizard and canvas saves", () => {
    const schema = [
      { column_name: "id", primitive_type: "integer" },
      { column_name: "name", primitive_type: "string" },
      { column_name: "joined_at", primitive_type: "datetime" },
      { column_name: "unknown_col", primitive_type: "jsonb" },
    ];

    const properties = buildInitialPropertiesFromSchema(schema, "id");

    expect(properties).toEqual([
      {
        source_column: "id",
        property_name: "id",
        semantic_type: "integer",
        included: true,
        is_primary_key: true,
      },
      {
        source_column: "name",
        property_name: "name",
        semantic_type: "string",
        included: true,
        is_primary_key: false,
      },
      {
        source_column: "joined_at",
        property_name: "joined_at",
        semantic_type: "datetime",
        included: true,
        is_primary_key: false,
      },
      {
        source_column: "unknown_col",
        property_name: "unknown_col",
        semantic_type: "string",
        included: true,
        is_primary_key: false,
      },
    ]);

    const request = buildMappingRequest({
      objectTypeId: "ot-1",
      properties,
      links: [],
      sourceNodes: [],
      computedProperties: [],
      layoutState: { node_a: { x: 10, y: 20 } },
    });

    expect(request).toEqual({
      object_type_id: "ot-1",
      properties,
      links: [],
      source_nodes: [],
      computed_properties: [],
      layout_state: { node_a: { x: 10, y: 20 } },
    });
  });
});
