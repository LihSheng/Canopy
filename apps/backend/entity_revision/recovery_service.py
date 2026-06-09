"""Binding recovery service for broken source bindings (Issue 3)."""

from datetime import UTC, datetime

from common.errors import NotFoundError
from entity_revision.domain import EntityRevision, SourceBinding
from entity_revision.repository import EntityRevisionRepository


class BindingRecoveryService:
    """Suggests and applies recovery mappings for broken source bindings."""

    def __init__(self, revision_repo: EntityRevisionRepository):
        self._revision_repo = revision_repo

    def get_recovery_suggestions(self, entity_id: str, draft_id: str) -> dict:
        """Return suggested field mappings for broken bindings in a draft.

        Suggestions are keyed by source_node_id, then by current source_field_name.
        Each suggestion contains {"suggested_field": str | None, "confidence": str}.
        """
        draft = self._revision_repo.get(draft_id)
        if draft is None or draft.entity_id != entity_id:
            raise NotFoundError("Draft not found")

        # Build a map of source_node_id -> available fields
        source_node_fields: dict[str, list[str]] = {}
        for sn in draft.source_nodes or []:
            fields = sn.get("fields") or []
            source_node_fields[sn.get("source_id", "")] = fields

        suggestions: dict[str, dict[str, dict]] = {}
        for binding in draft.source_bindings or []:
            node_id = binding.source_node_id
            available = source_node_fields.get(node_id, [])
            if binding.source_field_name in available:
                # Not broken
                continue

            # Try to match by property_key
            suggested = None
            confidence = "manual"
            if binding.property_key in available:
                suggested = binding.property_key
                confidence = "high"
            else:
                # Try case-insensitive match
                lower_available = {f.lower(): f for f in available}
                if binding.property_key.lower() in lower_available:
                    suggested = lower_available[binding.property_key.lower()]
                    confidence = "medium"

            if node_id not in suggestions:
                suggestions[node_id] = {}
            suggestions[node_id][binding.source_field_name] = {
                "suggested_field": suggested,
                "confidence": confidence,
            }

        return suggestions

    def apply_recovery(
        self,
        entity_id: str,
        draft_id: str,
        mapping: dict[str, dict[str, str]],
    ) -> EntityRevision:
        """Apply a recovery mapping to the draft's source bindings.

        *mapping* is a dict of {source_node_id: {old_field_name: new_field_name}}.
        """
        draft = self._revision_repo.get(draft_id)
        if draft is None or draft.entity_id != entity_id:
            raise NotFoundError("Draft not found")

        updated_bindings: list[SourceBinding] = []
        for binding in draft.source_bindings or []:
            node_id = binding.source_node_id
            old_field = binding.source_field_name
            new_field = mapping.get(node_id, {}).get(old_field)
            if new_field:
                updated_bindings.append(
                    SourceBinding(
                        property_key=binding.property_key,
                        source_node_id=binding.source_node_id,
                        source_field_name=new_field,
                        is_active=binding.is_active,
                    )
                )
            else:
                updated_bindings.append(binding)

        draft.source_bindings = updated_bindings
        draft.updated_at = datetime.now(UTC)
        return self._revision_repo.save(draft)
