import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from semantic.domain import ObjectType, PropertyMapping, SchemaColumn, SemanticMapping
from semantic.repository import ObjectTypeRepository, SemanticMappingRepository
from semantic.schema_service import DatasetSchemaService
from semantic.validation import (
    validate_mapping,
    validate_pk_sample,
)


class ObjectTypeService:
    def __init__(self, repo: ObjectTypeRepository):
        self._repo = repo

    def create(self, tenant_id: str, object_type_key: str, display_name: str, description: str = "") -> ObjectType:
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

    def get(self, id: str) -> ObjectType | None:
        return self._repo.get(id)

    def list_by_tenant(self, tenant_id: str) -> list[ObjectType]:
        return self._repo.list_by_tenant(tenant_id)

    def update(self, id: str, display_name: str | None = None, description: str | None = None) -> ObjectType:
        obj = self._repo.get(id)
        if obj is None:
            raise NotFoundError("Object type not found")
        if display_name is not None:
            obj.display_name = display_name
        if description is not None:
            obj.description = description
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

    def get_current(self, dataset_id: str, dataset_version_id: str) -> SemanticMapping | None:
        return self._mapping_repo.get_current(dataset_id, dataset_version_id)

    async def create(
        self,
        dataset_id: str,
        dataset_version_id: str,
        object_type_id: str,
        object_type_key: str,
        properties: list[PropertyMapping],
    ) -> SemanticMapping:
        # Validate object type exists
        obj_type = self._object_type_repo.get(object_type_id)
        if obj_type is None:
            raise NotFoundError("Object type not found")

        # Schema validation
        schema_columns: list[SchemaColumn] | None = None
        if self._schema_service:
            schema_columns = await self._schema_service.get_schema(dataset_id, dataset_version_id)

        # Run mapping validation
        errors = validate_mapping(properties, schema_columns)
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

        # Get next version number
        max_version = self._mapping_repo.get_max_version(dataset_id, dataset_version_id)
        version_number = max_version + 1

        now = datetime.now(UTC)
        mapping = SemanticMapping(
            id=str(uuid.uuid4()),
            tenant_id=obj_type.tenant_id,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            version_number=version_number,
            object_type_id=object_type_id,
            object_type_key=object_type_key,
            properties=properties,
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
    ) -> SemanticMapping:
        """Update creates a new version of the mapping."""
        return await self.create(dataset_id, dataset_version_id, object_type_id, object_type_key, properties)

    async def validate(
        self,
        dataset_id: str,
        dataset_version_id: str,
        properties: list[PropertyMapping],
    ) -> dict:
        """Validate mapping properties without persisting. Returns validation result."""
        schema_columns: list[SchemaColumn] | None = None
        if self._schema_service:
            schema_columns = await self._schema_service.get_schema(dataset_id, dataset_version_id)

        errors = validate_mapping(properties, schema_columns)

        # Also check PK sample
        if self._schema_service:
            pk_props = [p for p in properties if p.is_primary_key]
            if pk_props:
                pk_column = pk_props[0].source_column
                sample = await self._schema_service.get_column_sample(dataset_id, dataset_version_id, pk_column)
                pk_errors = validate_pk_sample(sample)
                errors.extend(pk_errors)

        return {"valid": len(errors) == 0, "errors": errors}
