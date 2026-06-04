"""Entity revision service — fork, publish, validate, lock management."""

import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from entity_revision.domain import (
    EntityProperty,
    EntityRevision,
    EntityRevisionDependency,
    RevisionStatus,
    SourceBinding,
)
from entity_revision.repository import EntityRevisionRepository
from semantic.repository import ObjectTypeRepository


class EntityRevisionService:
    """Orchestrates entity revision lifecycle: fork, draft, publish, lock."""

    def __init__(
        self,
        revision_repo: EntityRevisionRepository,
        object_type_repo: ObjectTypeRepository,
    ):
        self._revision_repo = revision_repo
        self._object_type_repo = object_type_repo

    # ── Fork draft from published ────────────────────────────────────────

    def fork_draft(
        self,
        entity_id: str,
        lock_holder_id: str,
        tenant_id: str,
    ) -> EntityRevision:
        """Create a new draft revision forked from the current published revision.

        Rules:
        - Entity must exist.
        - Must have at least one existing revision (published or otherwise)
          to fork from. If no published revision exists, fork from latest revision.
        - An active draft must not already exist (single active draft rule).
        - Locks the new draft to the requesting user.
        """
        # Verify entity exists
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        # Must have a published revision or at least some revision to fork from
        published = self._revision_repo.get_published(entity_id)
        if published is None:
            # No published revision; check if there are any revisions at all
            existing = self._revision_repo.list_by_entity(entity_id)
            if existing:
                published = existing[0]  # Fork from latest
            else:
                raise ValidationError(
                    "Cannot fork draft: entity has no published revision to fork from. "
                    "Create the entity with an initial revision first."
                )

        # Check for existing active draft
        existing_draft = self._revision_repo.get_draft(entity_id)
        if existing_draft is not None:
            raise ValidationError(
                f"An active draft already exists for this entity "
                f"(draft revision {existing_draft.revision_number}). "
                f"Discard it before creating a new draft."
            )

        # Create draft revision (copy of published)
        max_rev = self._revision_repo.get_max_revision_number(entity_id)
        now = datetime.now(UTC)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=max_rev + 1,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=published.id,
            properties=[
                EntityProperty(
                    property_id=p.property_id,
                    property_key=p.property_key,
                    display_name=p.display_name,
                    semantic_type=p.semantic_type,
                    is_required=p.is_required,
                    is_primary_key=p.is_primary_key,
                    sort_order=p.sort_order,
                )
                for p in published.properties
            ],
            source_bindings=[
                SourceBinding(
                    property_key=b.property_key,
                    source_node_id=b.source_node_id,
                    source_field_name=b.source_field_name,
                )
                for b in published.source_bindings
            ],
            links=published.links,
            source_nodes=published.source_nodes,
            computed_properties=published.computed_properties,
            layout_state=published.layout_state,
            lock_holder_id=lock_holder_id,
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        return self._revision_repo.save(draft)

    # ── Get draft ────────────────────────────────────────────────────────

    def get_draft(self, entity_id: str, tenant_id: str) -> EntityRevision | None:
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        return self._revision_repo.get_draft(entity_id)

    # ── Update draft ─────────────────────────────────────────────────────

    def update_draft(
        self,
        entity_id: str,
        tenant_id: str,
        properties: list[EntityProperty] | None = None,
        source_bindings: list[SourceBinding] | None = None,
        links: list[dict] | None = None,
        source_nodes: list[dict] | None = None,
        computed_properties: list[dict] | None = None,
        layout_state: dict | None = None,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Update an existing draft revision.

        Only the lock holder (or no lock) can update. If no draft exists, raises error.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        draft = self._revision_repo.get_draft(entity_id)
        if draft is None:
            raise NotFoundError("No active draft found for this entity")

        # Lock check: only lock holder can update
        if draft.lock_holder_id and lock_holder_id:
            if draft.lock_holder_id != lock_holder_id:
                raise ValidationError(
                    f"Draft is locked by another user. "
                    f"Only the lock holder ({draft.lock_holder_id}) can edit this draft."
                )

        now = datetime.now(UTC)

        if properties is not None:
            draft.properties = properties
        if source_bindings is not None:
            draft.source_bindings = source_bindings
        if links is not None:
            draft.links = links
        if source_nodes is not None:
            draft.source_nodes = source_nodes
        if computed_properties is not None:
            draft.computed_properties = computed_properties
        if layout_state is not None:
            draft.layout_state = layout_state

        draft.updated_at = now
        return self._revision_repo.save(draft)

    # ── Discard draft ────────────────────────────────────────────────────

    def discard_draft(self, entity_id: str, tenant_id: str, lock_holder_id: str | None = None) -> dict:
        """Delete the active draft revision, releasing the lock.

        Only the lock holder (or if no lock) can discard the draft.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        draft = self._revision_repo.get_draft(entity_id)
        if draft is None:
            raise NotFoundError("No active draft found for this entity")

        # Lock check: only lock holder (or no lock) can discard
        if draft.lock_holder_id and lock_holder_id:
            if draft.lock_holder_id != lock_holder_id:
                raise ValidationError(
                    f"Draft is locked by another user. "
                    f"Only the lock holder ({draft.lock_holder_id}) can discard this draft."
                )

        self._revision_repo.delete(draft.id)
        return {"discarded": True, "entity_id": entity_id, "draft_id": draft.id}

    # ── Property CRUD (within draft) ──────────────────────────────────────

    def add_property(
        self,
        entity_id: str,
        tenant_id: str,
        prop: EntityProperty,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Add a new property to the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        # Ensure property_id is set
        if not prop.property_id:
            prop.property_id = str(uuid.uuid4())
        # Check for duplicate property_key
        if any(p.property_key == prop.property_key for p in draft.properties):
            raise ValidationError(f"Property with key '{prop.property_key}' already exists.")
        # Assign sort_order if not specified
        if prop.sort_order == 0:
            max_order = max((p.sort_order for p in draft.properties), default=0)
            prop.sort_order = max_order + 1
        draft.properties.append(prop)
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def update_property(
        self,
        entity_id: str,
        tenant_id: str,
        property_id: str,
        updates: dict,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Update a single property in the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        for i, p in enumerate(draft.properties):
            if p.property_id == property_id:
                updated = EntityProperty(
                    property_id=p.property_id,
                    property_key=updates.get("property_key", p.property_key),
                    display_name=updates.get("display_name", p.display_name),
                    semantic_type=updates.get("semantic_type", p.semantic_type),
                    is_required=updates.get("is_required", p.is_required),
                    is_primary_key=updates.get("is_primary_key", p.is_primary_key),
                    sort_order=updates.get("sort_order", p.sort_order),
                )
                draft.properties[i] = updated
                draft.updated_at = datetime.now(UTC)
                return self._revision_repo.save(draft)
        raise NotFoundError(f"Property '{property_id}' not found in draft properties")

    def remove_property(
        self,
        entity_id: str,
        tenant_id: str,
        property_id: str,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Remove a property from the active draft. Also removes any bindings for it."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        # Find and remove the property
        found = False
        removed_key = ""
        for i, p in enumerate(draft.properties):
            if p.property_id == property_id:
                removed_key = p.property_key
                draft.properties.pop(i)
                found = True
                break
        if not found:
            raise NotFoundError(f"Property '{property_id}' not found in draft properties")
        # Remove any source bindings that reference this property_key
        if removed_key:
            draft.source_bindings = [b for b in draft.source_bindings if b.property_key != removed_key]
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def reorder_properties(
        self,
        entity_id: str,
        tenant_id: str,
        property_ids: list[str],
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Reorder properties in the draft to match the given property_id list order."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        id_to_prop = {p.property_id: p for p in draft.properties}
        reordered: list[EntityProperty] = []
        seen = set()
        for pid in property_ids:
            if pid in seen:
                raise ValidationError(f"Duplicate property_id '{pid}' in reorder list")
            seen.add(pid)
            if pid not in id_to_prop:
                raise NotFoundError(f"Property '{pid}' not found in draft properties")
            reordered.append(id_to_prop[pid])
        # Any properties not in the reorder list keep their relative order at end
        for p in draft.properties:
            if p.property_id not in seen:
                reordered.append(p)
        for i, p in enumerate(reordered):
            p.sort_order = i + 1
        draft.properties = reordered
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def _get_editable_draft(
        self,
        entity_id: str,
        tenant_id: str,
        lock_holder_id: str | None,
    ) -> EntityRevision:
        """Get the draft and validate it's editable by the lock holder."""
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        draft = self._revision_repo.get_draft(entity_id)
        if draft is None:
            raise NotFoundError("No active draft found for this entity")
        if draft.lock_holder_id and lock_holder_id:
            if draft.lock_holder_id != lock_holder_id:
                raise ValidationError(
                    f"Draft is locked by another user. "
                    f"Only the lock holder ({draft.lock_holder_id}) can edit this draft."
                )
        return draft

    # ── Publish draft ────────────────────────────────────────────────────

    def publish_draft(
        self,
        entity_id: str,
        tenant_id: str,
        source_dependencies: list[dict] | None = None,
    ) -> EntityRevision:
        """Publish the current draft, archiving the previously published revision.

        Publish validation rules:
        1. A draft must exist.
        2. At least one valid source binding must exist (source_nodes with source_node entries).
        3. All required properties must be present and not empty.
        4. All active bindings must pin to stable datasets/versions (if deps provided).
        5. Optional properties may remain unbound.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        draft = self._revision_repo.get_draft(entity_id)
        if draft is None:
            raise NotFoundError("No active draft found to publish")

        # ── Validate publish prerequisites ──

        errors: list[str] = []

        # Rule 1: At least one valid binding (source_nodes with at least one source)
        source_nodes = draft.source_nodes or []
        if len(source_nodes) == 0:
            errors.append(
                "Entity must have at least one source node binding to be published. "
                "Add a source node before publishing."
            )

        # Rule 2: All required properties must be present and have bindings
        required_props = [p for p in draft.properties if p.is_required]
        for rp in required_props:
            if not rp.property_key or not rp.property_key.strip():
                errors.append(f"Required property (id={rp.property_id}) has an empty property_key.")

            # Check that the required property has at least one source binding (prefer explicit bindings)
            if draft.source_bindings:
                bound = any(b.property_key == rp.property_key for b in draft.source_bindings)
            else:
                # Fallback to source_nodes.fields for backward compat
                bound = any(rp.property_key in (sn.get("fields") or []) for sn in source_nodes)
            if not bound:
                errors.append(
                    f"Required property '{rp.property_key}' ({rp.display_name}) "
                    f"has no source binding. "
                    f"Bind it to a source field before publishing."
                )

        # Rule 3: Source dependencies are always required for publish.
        # At least one dataset-level dependency must be pinned.
        if not source_dependencies:
            errors.append(
                "Publish requires at least one source dependency to be pinned. "
                "Provide a dataset-level dependency (dependency_type=dataset) so "
                "the published revision has a stable dependency contract."
            )
        else:
            has_dataset_level = any(d.get("dependency_type") == "dataset" for d in source_dependencies)
            if not has_dataset_level:
                errors.append(
                    "Publish requires at least one dataset-level dependency to be pinned. "
                    "Found dependencies but none with dependency_type=dataset."
                )

        if errors:
            raise ValidationError(f"Publish validation failed: {'; '.join(errors)}")

        # ── Execute publish ──

        now = datetime.now(UTC)
        previous_published = self._revision_repo.get_published(entity_id)

        # Archive previous published revision
        if previous_published is not None and previous_published.id != draft.id:
            previous_published.status = RevisionStatus.ARCHIVED.value
            previous_published.updated_at = now
            self._revision_repo.save(previous_published)

        # Promote draft to published
        draft.status = RevisionStatus.PUBLISHED.value
        draft.published_at = now
        draft.updated_at = now
        draft.lock_holder_id = None  # Release lock on publish
        draft.locked_at = None

        published = self._revision_repo.save(draft)

        # Pin source dependencies
        if source_dependencies:
            deps = [
                EntityRevisionDependency(
                    id=str(uuid.uuid4()),
                    revision_id=published.id,
                    dependency_type=d.get("dependency_type", "dataset"),
                    dependency_id=d["dependency_id"],
                )
                for d in source_dependencies
            ]
            self._revision_repo.save_dependencies(published.id, deps)

        return published

    # ── Revert to a prior revision ───────────────────────────────────────

    def revert_to_revision(
        self,
        entity_id: str,
        revision_id: str,
        tenant_id: str,
        lock_holder_id: str,
    ) -> EntityRevision:
        """Revert to a prior revision by creating a new draft based on it.

        Rules:
        - Entity must exist.
        - Target revision must exist and belong to the entity.
        - Target revision must not be a draft (cannot revert to a draft).
        - An active draft must not already exist (single active draft rule).
        - Creates a new draft with the target revision's full content.
        - Preserves history: original revision remains unchanged.
        - The new draft is locked to the requesting user for editing.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        # Fetch the target historical revision
        target = self._revision_repo.get(revision_id)
        if target is None:
            raise NotFoundError("Revision not found")
        if target.entity_id != entity_id:
            raise NotFoundError("Revision does not belong to this entity")
        if target.status == RevisionStatus.DRAFT.value:
            raise ValidationError("Cannot revert to a draft revision. Select a published or archived revision.")

        # Check for existing active draft
        existing_draft = self._revision_repo.get_draft(entity_id)
        if existing_draft is not None:
            raise ValidationError(
                f"An active draft already exists for this entity "
                f"(draft revision {existing_draft.revision_number}). "
                f"Discard it before reverting to a prior version."
            )

        # Create a new draft based on the target revision content
        max_rev = self._revision_repo.get_max_revision_number(entity_id)
        now = datetime.now(UTC)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=max_rev + 1,
            status=RevisionStatus.DRAFT.value,
            forked_from_revision_id=target.id,
            properties=[
                EntityProperty(
                    property_id=p.property_id,
                    property_key=p.property_key,
                    display_name=p.display_name,
                    semantic_type=p.semantic_type,
                    is_required=p.is_required,
                    is_primary_key=p.is_primary_key,
                    sort_order=p.sort_order,
                )
                for p in target.properties
            ],
            source_bindings=[
                SourceBinding(
                    property_key=b.property_key,
                    source_node_id=b.source_node_id,
                    source_field_name=b.source_field_name,
                )
                for b in target.source_bindings
            ],
            links=target.links,
            source_nodes=target.source_nodes,
            computed_properties=target.computed_properties,
            layout_state=target.layout_state,
            lock_holder_id=lock_holder_id,
            locked_at=now,
            created_at=now,
            updated_at=now,
        )
        return self._revision_repo.save(draft)

    # ── Get single revision ──────────────────────────────────────────────

    def get_revision(
        self,
        entity_id: str,
        revision_id: str,
        tenant_id: str,
    ) -> EntityRevision:
        """Get a specific revision by ID, verifying it belongs to the entity."""
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        revision = self._revision_repo.get(revision_id)
        if revision is None:
            raise NotFoundError("Revision not found")
        if revision.entity_id != entity_id:
            raise NotFoundError("Revision does not belong to this entity")
        return revision

    # ── List revisions ───────────────────────────────────────────────────

    def list_revisions(self, entity_id: str, tenant_id: str) -> list[EntityRevision]:
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        return self._revision_repo.list_by_entity(entity_id)

    # ── Create initial revision (blank canvas) ───────────────────────────

    def create_initial_revision(
        self,
        entity_id: str,
        tenant_id: str,
        properties: list[EntityProperty] | None = None,
        source_bindings: list[SourceBinding] | None = None,
        links: list[dict] | None = None,
        source_nodes: list[dict] | None = None,
        computed_properties: list[dict] | None = None,
        layout_state: dict | None = None,
        lock_holder_id: str | None = None,
        publish: bool = False,
        source_dependencies: list[dict] | None = None,
    ) -> EntityRevision:
        """Create the first revision for an entity (blank canvas or with initial content).

        If published directly, skips draft and goes straight to published.
        Otherwise creates a draft revision.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        existing_count = self._revision_repo.count_by_entity(entity_id)
        if existing_count > 0:
            raise ValidationError("Entity already has revisions. Use fork_draft() to create a new draft.")

        now = datetime.now(UTC)

        revision = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value if publish else RevisionStatus.DRAFT.value,
            properties=properties or [],
            source_bindings=source_bindings or [],
            links=links or [],
            source_nodes=source_nodes or [],
            computed_properties=computed_properties or [],
            layout_state=layout_state or {},
            lock_holder_id=None if publish else lock_holder_id,
            locked_at=None if publish else now,
            created_at=now,
            updated_at=now,
            published_at=now if publish else None,
        )

        saved = self._revision_repo.save(revision)

        # Pin dependencies on initial publish
        if publish and source_dependencies:
            deps = [
                EntityRevisionDependency(
                    id=str(uuid.uuid4()),
                    revision_id=saved.id,
                    dependency_type=d.get("dependency_type", "dataset"),
                    dependency_id=d["dependency_id"],
                )
                for d in source_dependencies
            ]
            self._revision_repo.save_dependencies(saved.id, deps)

        return saved

    # ── Get entity status summary ─────────────────────────────────────────

    def get_entity_status(self, entity_id: str) -> dict:
        """Return a summary of the entity's revision state.

        Returns { has_published: bool, has_draft: bool, lock_holder_id: str|None,
                  published_revision_number: int|None, draft_revision_number: int|None }
        """
        published = self._revision_repo.get_published(entity_id)
        draft = self._revision_repo.get_draft(entity_id)

        return {
            "has_published": published is not None,
            "has_draft": draft is not None,
            "lock_holder_id": draft.lock_holder_id if draft else None,
            "published_revision_number": published.revision_number if published else None,
            "draft_revision_number": draft.revision_number if draft else None,
            "published_at": published.published_at.isoformat() if published and published.published_at else None,
        }
