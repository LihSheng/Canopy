import type {
  ComputedProperty,
  EntityLink,
  PropertyMapping,
  SchemaColumn,
  SourceNode,
} from "@/lib/api/types";

export type MappingLayoutState = Record<string, { x: number; y: number }>;

export function getDefaultSemanticType(primitiveType?: string | null): string {
  switch (primitiveType) {
    case "integer":
    case "number":
    case "boolean":
    case "datetime":
    case "date":
    case "string":
      return primitiveType;
    default:
      return "string";
  }
}

export function buildInitialPropertiesFromSchema(
  schemaColumns: SchemaColumn[],
  primaryKeyColumn: string,
): PropertyMapping[] {
  return schemaColumns.map((col) => ({
    source_column: col.column_name,
    property_name: col.column_name,
    semantic_type: getDefaultSemanticType(col.primitive_type),
    included: true,
    is_primary_key: col.column_name === primaryKeyColumn,
  }));
}

type BuildMappingRequestArgs = {
  objectTypeId: string;
  properties: PropertyMapping[];
  links?: EntityLink[];
  sourceNodes?: SourceNode[];
  computedProperties?: ComputedProperty[];
  layoutState?: MappingLayoutState;
};

export function buildMappingRequest({
  objectTypeId,
  properties,
  links,
  sourceNodes,
  computedProperties,
  layoutState,
}: BuildMappingRequestArgs): {
  object_type_id: string;
  properties: PropertyMapping[];
  links: EntityLink[];
  source_nodes: SourceNode[];
  computed_properties: ComputedProperty[];
  layout_state: MappingLayoutState;
} {
  return {
    object_type_id: objectTypeId,
    properties,
    links: links ?? [],
    source_nodes: sourceNodes ?? [],
    computed_properties: computedProperties ?? [],
    layout_state: layoutState ?? {},
  };
}
