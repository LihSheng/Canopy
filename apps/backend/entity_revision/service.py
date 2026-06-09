"""Entity revision service — fork, publish, validate, lock management."""

import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from entity_formula_engine.engine import FormulaEngine
from entity_revision.domain import (
    ComputedProperty,
    EntityLink,
    EntityProperty,
    EntityRevision,
    EntityRevisionDependency,
    LinkCardinality,
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
                    is_active=b.is_active,
                )
                for b in published.source_bindings
            ],
            planned_bindings=[
                SourceBinding(
                    property_key=b.property_key,
                    source_node_id=b.source_node_id,
                    source_field_name=b.source_field_name,
                    is_active=b.is_active,
                )
                for b in published.planned_bindings
            ],
            links=published.links,
            source_nodes=published.source_nodes,
            computed_properties=[
                ComputedProperty(
                    id=cp.id,
                    property_key=cp.property_key,
                    display_name=cp.display_name,
                    formula=cp.formula,
                    formula_type=cp.formula_type,
                    inputs=cp.inputs,
                    output_type=cp.output_type,
                    sort_order=cp.sort_order,
                    is_active=cp.is_active,
                )
                for cp in published.computed_properties
            ],
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
        planned_bindings: list[SourceBinding] | None = None,
        links: list[dict] | None = None,
        source_nodes: list[dict] | None = None,
        computed_properties: list[ComputedProperty] | None = None,
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

        # Immutability guard: only drafts can be mutated
        if draft.status != RevisionStatus.DRAFT.value:
            raise ValidationError(f"Cannot mutate a {draft.status} revision. Only draft revisions are editable.")

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
        if planned_bindings is not None:
            draft.planned_bindings = planned_bindings
        if links is not None:
            draft.links = [EntityLink.from_dict(lnk) for lnk in links]
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
            draft.planned_bindings = [b for b in draft.planned_bindings if b.property_key != removed_key]
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

    # ── Link CRUD (within draft) ───────────────────────────────────────────

    def add_link(
        self,
        entity_id: str,
        tenant_id: str,
        link: EntityLink,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Add a new link to the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        # Ensure link_id is set
        if not link.link_id:
            link.link_id = str(uuid.uuid4())
        # Check for duplicate link_id
        if any(lnk.link_id == link.link_id for lnk in draft.links):
            raise ValidationError(f"Link with id '{link.link_id}' already exists.")
        draft.links.append(link)
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def update_link(
        self,
        entity_id: str,
        tenant_id: str,
        link_id: str,
        updates: dict,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Update a single link in the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        for i, lnk in enumerate(draft.links):
            if lnk.link_id == link_id:
                updated = EntityLink(
                    link_id=lnk.link_id,
                    display_name=updates.get("display_name", lnk.display_name),
                    source_property_key=updates.get("source_property_key", lnk.source_property_key),
                    target_entity_id=updates.get("target_entity_id", lnk.target_entity_id),
                    target_property_key=updates.get("target_property_key", lnk.target_property_key),
                    cardinality=updates.get("cardinality", lnk.cardinality),
                    is_optional=updates.get("is_optional", lnk.is_optional),
                    is_active=updates.get("is_active", lnk.is_active),
                )
                draft.links[i] = updated
                draft.updated_at = datetime.now(UTC)
                return self._revision_repo.save(draft)
        raise NotFoundError(f"Link '{link_id}' not found in draft links")

    def remove_link(
        self,
        entity_id: str,
        tenant_id: str,
        link_id: str,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Remove a link from the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        found = False
        for i, lnk in enumerate(draft.links):
            if lnk.link_id == link_id:
                draft.links.pop(i)
                found = True
                break
        if not found:
            raise NotFoundError(f"Link '{link_id}' not found in draft links")
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def list_links(self, entity_id: str, tenant_id: str) -> list[EntityLink]:
        """Return links from the active draft or published revision."""
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        draft = self._revision_repo.get_draft(entity_id)
        if draft is not None:
            return [lnk if isinstance(lnk, EntityLink) else EntityLink.from_dict(lnk) for lnk in draft.links]
        published = self._revision_repo.get_published(entity_id)
        if published is not None:
            return [lnk if isinstance(lnk, EntityLink) else EntityLink.from_dict(lnk) for lnk in published.links]
        return []

    # ── Computed Property CRUD (within draft) ──────────────────────────────

    def add_computed_property(
        self,
        entity_id: str,
        tenant_id: str,
        prop: ComputedProperty,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Add a computed property to the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        if not prop.id:
            prop.id = str(uuid.uuid4())
        self._validate_computed_property(draft, prop)
        draft.computed_properties.append(prop)
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def update_computed_property(
        self,
        entity_id: str,
        tenant_id: str,
        computed_property_id: str,
        updates: dict,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Update a computed property in the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        for i, cp in enumerate(draft.computed_properties):
            if cp.id == computed_property_id:
                updated = ComputedProperty(
                    id=cp.id,
                    property_key=updates.get("property_key", cp.property_key),
                    display_name=updates.get("display_name", cp.display_name),
                    formula=updates.get("formula", cp.formula),
                    formula_type=updates.get("formula_type", cp.formula_type),
                    inputs=updates.get("inputs", cp.inputs),
                    output_type=updates.get("output_type", cp.output_type),
                    sort_order=updates.get("sort_order", cp.sort_order),
                    is_active=updates.get("is_active", cp.is_active),
                )
                self._validate_computed_property(draft, updated)
                draft.computed_properties[i] = updated
                draft.updated_at = datetime.now(UTC)
                return self._revision_repo.save(draft)
        raise NotFoundError(f"Computed property '{computed_property_id}' not found")

    def remove_computed_property(
        self,
        entity_id: str,
        tenant_id: str,
        computed_property_id: str,
        lock_holder_id: str | None = None,
    ) -> EntityRevision:
        """Remove a computed property from the active draft."""
        draft = self._get_editable_draft(entity_id, tenant_id, lock_holder_id)
        found = False
        for i, cp in enumerate(draft.computed_properties):
            if cp.id == computed_property_id:
                draft.computed_properties.pop(i)
                found = True
                break
        if not found:
            raise NotFoundError(f"Computed property '{computed_property_id}' not found")
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)

    def list_computed_properties(self, entity_id: str, tenant_id: str) -> list[ComputedProperty]:
        """Return computed properties from the active draft or published revision."""
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")
        draft = self._revision_repo.get_draft(entity_id)
        if draft is not None:
            return draft.computed_properties
        published = self._revision_repo.get_published(entity_id)
        if published is not None:
            return published.computed_properties
        return []

    def _validate_computed_property(self, draft: EntityRevision, prop: ComputedProperty) -> None:
        """Ensure computed property references only valid property keys and has valid syntax."""
        property_keys = {p.property_key for p in draft.properties}
        # Validate formula syntax first (catches unknown functions, unbalanced parens, cross-entity refs)
        self._validate_computed_property_syntax(prop.formula)
        # Validate inputs exist in properties
        for inp in prop.inputs or []:
            if inp not in property_keys:
                raise ValidationError(f"Computed property '{prop.property_key}' references unknown property '{inp}'.")
        # Validate formula references only existing properties and inputs
        try:
            refs = FormulaEngine().extract_property_references(prop.formula)
        except ValidationError as e:
            raise ValidationError(f"Computed property '{prop.property_key}' formula syntax error: {e}")
        for ref in refs:
            if ref not in property_keys:
                raise ValidationError(f"Computed property '{prop.property_key}' references unknown property '{ref}'.")
            if ref not in (prop.inputs or []):
                raise ValidationError(
                    f"Computed property '{prop.property_key}' formula references "
                    f"property '{ref}' which is not listed in inputs."
                )

    def _validate_computed_property_syntax(self, formula: str) -> None:
        """Basic syntax validation: reject empty formulas and parse with engine."""
        if not formula or not formula.strip():
            raise ValidationError("Computed property formula cannot be empty.")
        try:
            FormulaEngine().evaluate(formula, inputs=[], row_data={})
        except ValidationError as e:
            raise ValidationError(f"Computed property formula syntax error: {e}")

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

        # Immutability guard: only drafts can be edited
        if draft.status != RevisionStatus.DRAFT.value:
            raise ValidationError(f"Cannot edit a {draft.status} revision. Only draft revisions are editable.")

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
        4. Optional source dependency pinning is accepted when provided.
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

        # Rule 3: Link cardinality and target validation
        for raw_link in draft.links or []:
            try:
                link = raw_link if isinstance(raw_link, EntityLink) else EntityLink.from_dict(raw_link)
            except ValueError as ve:
                errors.append(str(ve))
                continue
            if link.cardinality not in {LinkCardinality.ONE_TO_ONE.value, LinkCardinality.ONE_TO_MANY.value}:
                errors.append(
                    f"Link '{link.link_id}' has invalid cardinality '{link.cardinality}'. "
                    f"Only '{LinkCardinality.ONE_TO_ONE.value}' and '{LinkCardinality.ONE_TO_MANY.value}' are allowed."
                )
                continue
            target_published = self._revision_repo.get_published(link.target_entity_id)
            if target_published is None:
                if not link.is_optional:
                    errors.append(
                        f"Link '{link.link_id}' references target entity "
                        f"'{link.target_entity_id}' which is not published."
                    )
                continue
            source_keys = {p.property_key for p in draft.properties}
            if link.source_property_key not in source_keys:
                errors.append(
                    f"Link '{link.link_id}' source_property_key "
                    f"'{link.source_property_key}' does not exist in entity properties."
                )
            if target_published is not None:
                target_keys = {p.property_key for p in target_published.properties}
                if link.target_property_key not in target_keys:
                    errors.append(
                        f"Link '{link.link_id}' target_property_key "
                        f"'{link.target_property_key}' does not exist in target entity properties."
                    )

        # Rule 4: Planned bindings must reference published entities
        for pb in draft.planned_bindings or []:
            target_published = self._revision_repo.get_published(pb.source_node_id)
            if target_published is None:
                errors.append(
                    f"Planned binding for property '{pb.property_key}' references "
                    f"an unpublished entity ({pb.source_node_id}). "
                    f"The target entity must be published before this entity can be published."
                )

        # Rule 5: Computed property semantic validation
        property_keys = {p.property_key for p in draft.properties}
        computed_keys = {cp.property_key for cp in draft.computed_properties if cp.is_active}
        for cp in draft.computed_properties or []:
            if not cp.is_active:
                continue
            # Check all inputs exist in base properties
            for inp in cp.inputs or []:
                if inp not in property_keys:
                    errors.append(
                        f"Computed property '{cp.property_key}' references removed or renamed property '{inp}'."
                    )
            # Check formula references only base properties (no circular deps)
            try:
                refs = FormulaEngine().extract_property_references(cp.formula)
            except ValidationError as e:
                errors.append(f"Computed property '{cp.property_key}' formula syntax error: {e}")
                continue
            for ref in refs:
                if ref in computed_keys:
                    errors.append(
                        f"Computed property '{cp.property_key}' references another computed property '{ref}'. "
                        f"Circular dependencies are not allowed."
                    )
            # Check output type mismatch (best-effort inference)
            inferred = FormulaEngine().infer_output_type(cp.formula)
            if inferred and inferred != cp.output_type:
                errors.append(
                    f"Computed property '{cp.property_key}' output type mismatch: "
                    f"formula produces {inferred} but declared output_type is {cp.output_type}."
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

        # Transition entity status to "published" on first publish
        obj = self._object_type_repo.get(entity_id, tenant_id=None)
        if obj is not None and obj.status != "published":
            obj.status = "published"
            obj.updated_at = now
            self._object_type_repo.save(obj)

        # Pin source dependencies when the caller provides them.
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

    # ── Computed property warnings (draft state) ─────────────────────────

    def get_computed_property_warnings(self, entity_id: str) -> list[str]:
        """Return warnings for computed properties in the active draft.

        Warns if a computed property references a property that has been removed
        or whose property_key has changed.
        """
        draft = self._revision_repo.get_draft(entity_id)
        if draft is None:
            return []
        return self._check_computed_property_dependencies(draft)

    def _check_computed_property_dependencies(self, draft: EntityRevision) -> list[str]:
        """Return warnings for computed properties that reference missing or renamed properties."""
        property_keys = {p.property_key for p in draft.properties}
        warnings: list[str] = []
        for cp in draft.computed_properties or []:
            if not cp.is_active:
                continue
            try:
                refs = FormulaEngine().extract_property_references(cp.formula)
            except ValidationError:
                continue
            for ref in refs:
                if ref not in property_keys:
                    warnings.append(
                        f"Computed property '{cp.property_key}' references "
                        f"property '{ref}' which is missing or renamed."
                    )
        return warnings

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
                    is_active=b.is_active,
                )
                for b in target.source_bindings
            ],
            planned_bindings=[
                SourceBinding(
                    property_key=b.property_key,
                    source_node_id=b.source_node_id,
                    source_field_name=b.source_field_name,
                    is_active=b.is_active,
                )
                for b in target.planned_bindings
            ],
            links=target.links,
            source_nodes=target.source_nodes,
            computed_properties=[
                ComputedProperty(
                    id=cp.id,
                    property_key=cp.property_key,
                    display_name=cp.display_name,
                    formula=cp.formula,
                    formula_type=cp.formula_type,
                    inputs=cp.inputs,
                    output_type=cp.output_type,
                    sort_order=cp.sort_order,
                    is_active=cp.is_active,
                )
                for cp in target.computed_properties
            ],
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
        planned_bindings: list[SourceBinding] | None = None,
        links: list[dict] | None = None,
        source_nodes: list[dict] | None = None,
        computed_properties: list[ComputedProperty] | None = None,
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
            planned_bindings=planned_bindings or [],
            links=[EntityLink.from_dict(lnk) for lnk in links] if links else [],
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

        # Transition entity status to "published" on initial publish
        if publish:
            if obj.status != "published":
                obj.status = "published"
                obj.updated_at = now
                self._object_type_repo.save(obj)

        # Pin dependencies on initial publish when provided.
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

    # ── Runtime reader (version pinning) ──────────────────────────────────

    def get_latest_published_entity(self, entity_id: str, tenant_id: str) -> EntityRevision:
        """Return the current active published EntityRevision for runtime consumption.

        Raises NotFoundError if the entity or its published revision does not exist.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        published = self._revision_repo.get_published(entity_id)
        if published is None:
            raise NotFoundError("No published revision found for this entity")
        return published

    def get_entity_at_version(self, entity_id: str, revision_number: int, tenant_id: str) -> EntityRevision:
        """Return a specific published or archived revision by revision_number.

        Only published and archived revisions are exposed for runtime pinning.
        Drafts are not pinnable. Raises NotFoundError if not found or is a draft.
        """
        obj = self._object_type_repo.get(entity_id, tenant_id=tenant_id)
        if obj is None:
            raise NotFoundError("Entity not found")

        revisions = self._revision_repo.list_by_entity(entity_id)
        for rev in revisions:
            if rev.revision_number == revision_number:
                if rev.status == RevisionStatus.DRAFT.value:
                    raise NotFoundError("Draft revisions cannot be pinned")
                return rev

        raise NotFoundError(f"Revision number {revision_number} not found for this entity")

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
