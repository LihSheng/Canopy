import re
import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from semantic.domain import (
    ComputedProperty,
    EntityLink,
    ObjectType,
    PropertyMapping,
    SchemaColumn,
    SemanticMapping,
    SourceNode,
)
from semantic.repository import ObjectTypeRepository, SemanticMappingRepository
from semantic.schema_service import DatasetSchemaService
from semantic.validation import (
    validate_computed_properties,
    validate_links,
    validate_mapping,
    validate_pk_sample,
)

# ─── Type compatibility matrix ───
# Maps source semantic_type -> set of compatible target semantic types.
_TYPE_COMPATIBILITY: dict[str, set[str]] = {
    "string": {"string"},
    "integer": {"integer", "number"},
    "number": {"number", "integer"},
    "boolean": {"boolean"},
    "datetime": {"datetime", "date"},
    "date": {"date", "datetime"},
}


def _resolve_target_key(
    mapping_repo: SemanticMappingRepository,
    tenant_id: str,
    target_object_type_id: str,
) -> tuple[str | None, str | None]:
    """Resolve target primary key from the latest mapping of target_object_type_id.

    Returns (target_property_key, target_semantic_type) or (None, None) if not found.
    """
    target_mapping = mapping_repo.get_latest_by_object_type_id(tenant_id, target_object_type_id)
    if target_mapping is None:
        return None, None
    pk_props = [p for p in target_mapping.properties if p.is_primary_key]
    if not pk_props:
        return None, None
    pk = pk_props[0]
    return pk.property_name, pk.semantic_type


def _check_type_compatibility(source_type: str, target_type: str) -> bool:
    """Check if source semantic type is compatible with target semantic type."""
    compatible = _TYPE_COMPATIBILITY.get(source_type, set())
    return target_type in compatible


def _generate_object_type_key(display_name: str, repo: ObjectTypeRepository, tenant_id: str) -> str:
    """Generate a stable, unique object_type_key from a display name.

    Rules:
    - Lowercase, replace non-alphanumeric with underscores
    - Collapse multiple underscores
    - Strip leading/trailing underscores
    - Prepend 'entity_' if the result starts with a digit
    - Ensure uniqueness by appending a suffix if needed
    """
    key = display_name.lower().strip()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    key = re.sub(r"_+", "_", key)
    key = key.strip("_")
    if not key:
        key = "entity"
    if key[0].isdigit():
        key = "entity_" + key

    # Ensure uniqueness within tenant
    base_key = key
    suffix = 1
    while repo.get_by_key(tenant_id, key) is not None:
        key = f"{base_key}_{suffix}"
        suffix += 1
    return key


class ObjectTypeService:
    def __init__(self, repo: ObjectTypeRepository):
        self._repo = repo

    def create(self, tenant_id: str, object_type_key: str, display_name: str, description: str = "") -> ObjectType:
        # Pre-check for duplicate key (avoids IntegrityError -> proper 409)
        existing = self._repo.get_by_key(tenant_id, object_type_key)
        if existing is not None:
            raise ValueError(f"Object type key '{object_type_key}' already exists for this tenant")
        now = datetime.now(UTC)
        obj_type = ObjectType(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            object_type_key=object_type_key,
            display_name=display_name,
            description=description,
            created_at=now,
        )
        return self._repo.save(obj_type)

    def create_entity(
        self,
        tenant_id: str,
        display_name: str,
        description: str = "",
        plural_name: str = "",
        icon: str = "",
        groups: list[str] | None = None,
    ) -> ObjectType:
        """Create an entity shell with server-generated object_type_key.

        Follows the Palantir-style helper flow: key is generated from display_name
        once and stays fixed afterward.
        """
        key = _generate_object_type_key(display_name, self._repo, tenant_id)
        now = datetime.now(UTC)
        obj_type = ObjectType(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            object_type_key=key,
            display_name=display_name,
            description=description,
            plural_name=plural_name,
            icon=icon,
            groups=groups or [],
            status="in_progress",
            created_at=now,
        )
        return self._repo.save(obj_type)

    def get(self, id: str, tenant_id: str) -> ObjectType | None:
        return self._repo.get(id, tenant_id=tenant_id)

    def list_by_tenant(self, tenant_id: str) -> list[ObjectType]:
        return self._repo.list_by_tenant(tenant_id)

    def update(
        self,
        id: str,
        tenant_id: str,
        display_name: str | None = None,
        description: str | None = None,
        plural_name: str | None = None,
        icon: str | None = None,
        groups: list[str] | None = None,
    ) -> ObjectType:
        obj = self._repo.get(id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Object type not found")
        if display_name is not None:
            obj.display_name = display_name
        if description is not None:
            obj.description = description
        if plural_name is not None:
            obj.plural_name = plural_name
        if icon is not None:
            obj.icon = icon
        if groups is not None:
            obj.groups = groups
        obj.updated_at = datetime.now(UTC)
        return self._repo.save(obj)


class SemanticMappingService:
    def __init__(
        self,
        mapping_repo: SemanticMappingRepository,
        object_type_repo: ObjectTypeRepository,
        schema_service: DatasetSchemaService | None = None,
    ):
        self._mapping_repo = mapping_repo
        self._object_type_repo = object_type_repo
        self._schema_service = schema_service

    def get_current(
        self, dataset_id: str, dataset_version_id: str, tenant_id: str | None = None
    ) -> SemanticMapping | None:
        return self._mapping_repo.get_current(dataset_id, dataset_version_id, tenant_id=tenant_id)

    async def create(
        self,
        dataset_id: str,
        dataset_version_id: str,
        object_type_id: str,
        object_type_key: str,
        properties: list[PropertyMapping],
        links: list[EntityLink] | None = None,
        source_nodes: list[SourceNode] | None = None,
        computed_properties: list[ComputedProperty] | None = None,
        layout_state: dict | None = None,
        tenant_id: str | None = None,
    ) -> SemanticMapping:
        # Validate object type exists and belongs to the correct tenant
        obj_type = self._object_type_repo.get(object_type_id, tenant_id=tenant_id)
        if obj_type is None:
            raise NotFoundError("Object type not found")

        # Derive object_type_key from the validated Object Type (never trust client)
        object_type_key = obj_type.object_type_key

        links = links or []
        source_nodes = source_nodes or []
        computed_properties = computed_properties or []
        layout_state = layout_state or {}
        tenant_id = obj_type.tenant_id

        # Schema validation
        schema_columns: list[SchemaColumn] | None = None
        if self._schema_service:
            schema_columns = await self._schema_service.get_schema(dataset_id, dataset_version_id)
            # Treat empty schema as unknown/unavailable. Validation endpoint should stay
            # useful even when dataset/version isn't seeded in tests or schema isn't ready yet.
            if not schema_columns:
                schema_columns = None

        # Run all validation (stateless + I/O-bound)
        errors = validate_mapping(properties, schema_columns)
        errors.extend(validate_links(links, properties))
        errors.extend(validate_computed_properties(computed_properties, properties, source_nodes))
        link_type_errors = await self._validate_link_type_compatibility(links, properties, tenant_id)
        errors.extend(link_type_errors)

        if errors:
            raise ValidationError(f"Validation failed: {errors}")

        # Run PK sample validation
        if self._schema_service:
            pk_props = [p for p in properties if p.is_primary_key]
            if pk_props:
                pk_column = pk_props[0].source_column
                sample = await self._schema_service.get_column_sample(dataset_id, dataset_version_id, pk_column)
                pk_errors = validate_pk_sample(sample)
                if pk_errors:
                    raise ValidationError(f"Primary key validation failed: {pk_errors}")

        # Resolve target keys and build links with resolved PKs
        resolved_links = await self._resolve_link_targets(links, tenant_id)

        # Get next version number
        max_version = self._mapping_repo.get_max_version(dataset_id, dataset_version_id)
        version_number = max_version + 1

        now = datetime.now(UTC)
        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            version_number=version_number,
            object_type_id=object_type_id,
            object_type_key=object_type_key,
            properties=properties,
            links=resolved_links,
            source_nodes=source_nodes,
            computed_properties=computed_properties,
            layout_state=layout_state,
            created_at=now,
        )
        return self._mapping_repo.save(mapping)

    async def update(
        self,
        dataset_id: str,
        dataset_version_id: str,
        object_type_id: str,
        object_type_key: str,
        properties: list[PropertyMapping],
        links: list[EntityLink] | None = None,
        source_nodes: list[SourceNode] | None = None,
        computed_properties: list[ComputedProperty] | None = None,
        layout_state: dict | None = None,
        tenant_id: str | None = None,
    ) -> SemanticMapping:
        """Update creates a new version of the mapping."""
        return await self.create(
            dataset_id,
            dataset_version_id,
            object_type_id,
            object_type_key,
            properties,
            links=links,
            source_nodes=source_nodes,
            computed_properties=computed_properties,
            layout_state=layout_state,
            tenant_id=tenant_id,
        )

    async def validate(
        self,
        dataset_id: str,
        dataset_version_id: str,
        properties: list[PropertyMapping],
        object_type_id: str | None = None,
        links: list[EntityLink] | None = None,
        computed_properties: list[ComputedProperty] | None = None,
        source_nodes: list[SourceNode] | None = None,
        tenant_id: str | None = None,
    ) -> dict:
        """Validate mapping properties without persisting. Returns validation result."""
        links = links or []
        errors: list[dict] = []

        # Validate object type exists and belongs to tenant when provided
        if object_type_id:
            obj_type = self._object_type_repo.get(object_type_id, tenant_id=tenant_id)
            if obj_type is None:
                errors.append(
                    {
                        "field": "object_type_id",
                        "value": object_type_id,
                        "message": "Object type not found or does not belong to this tenant",
                    }
                )

        schema_columns: list[SchemaColumn] | None = None
        if self._schema_service:
            schema_columns = await self._schema_service.get_schema(dataset_id, dataset_version_id)

        errors.extend(validate_mapping(properties, schema_columns))

        # Also check PK sample (only when schema is available)
        if self._schema_service and schema_columns is not None:
            pk_props = [p for p in properties if p.is_primary_key]
            if pk_props:
                pk_column = pk_props[0].source_column
                sample = await self._schema_service.get_column_sample(dataset_id, dataset_version_id, pk_column)
                pk_errors = validate_pk_sample(sample)
                errors.extend(pk_errors)

        # Link validation (stateless + type compatibility)
        errors.extend(validate_links(links, properties))

        # Computed property validation
        errors.extend(validate_computed_properties(computed_properties or [], properties, source_nodes or []))

        # Type compatibility check requires tenant context
        if tenant_id:
            link_type_errors = await self._validate_link_type_compatibility(links, properties, tenant_id)
            errors.extend(link_type_errors)

        return {"valid": len(errors) == 0, "errors": errors}

    async def _resolve_link_targets(
        self,
        links: list[EntityLink],
        tenant_id: str,
    ) -> list[EntityLink]:
        """Resolve target_property_key for each link by looking up the target PK."""
        resolved: list[EntityLink] = []
        for link in links:
            target_pk, _ = _resolve_target_key(self._mapping_repo, tenant_id, link.target_object_type_id)
            resolved.append(
                EntityLink(
                    link_id=link.link_id,
                    display_name=link.display_name,
                    source_property_key=link.source_property_key,
                    target_object_type_id=link.target_object_type_id,
                    target_property_key=target_pk or link.target_property_key,
                    cardinality=link.cardinality,
                )
            )
        return resolved

    async def _validate_link_type_compatibility(
        self,
        links: list[EntityLink],
        properties: list[PropertyMapping],
        tenant_id: str,
    ) -> list[dict]:
        """Validate type compatibility between source property and target PK for each link."""
        errors: list[dict] = []
        prop_by_name: dict[str, PropertyMapping] = {p.property_name: p for p in properties}

        for i, link in enumerate(links):
            target_pk, target_type = _resolve_target_key(self._mapping_repo, tenant_id, link.target_object_type_id)

            if target_pk is None:
                errors.append(
                    {
                        "field": f"links[{i}].target_object_type_id",
                        "value": link.target_object_type_id,
                        "message": (
                            f"No primary key found for target object type "
                            f"'{link.target_object_type_id}'. "
                            "Ensure the target entity has a primary key configured."
                        ),
                    }
                )
                continue

            assert target_type is not None, "target_type should be present when target_pk is resolved"

            source_prop = prop_by_name.get(link.source_property_key)
            if source_prop is None:
                # Already caught by validate_links -> validate_link_excluded_properties
                continue

            source_type = source_prop.semantic_type
            if not _check_type_compatibility(source_type, target_type):
                errors.append(
                    {
                        "field": f"links[{i}].source_property_key",
                        "value": link.source_property_key,
                        "message": (
                            f"Key compatibility error: source property '{link.source_property_key}' "
                            f"(type: {source_type}) is not compatible with target primary key "
                            f"'{target_pk}' (type: {target_type})"
                        ),
                    }
                )

        return errors
