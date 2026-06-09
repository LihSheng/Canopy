"""Link resolver service — runtime resolution of entity links."""

from common.errors import NotFoundError
from entity_materialization.service import EntityMaterializationService
from entity_revision.domain import EntityLink, EntityRevision, LinkCardinality
from entity_revision.repository import EntityRevisionRepository


class LinkResolverService:
    """Resolves direct links between published entities at runtime."""

    def __init__(
        self,
        revision_repo: EntityRevisionRepository,
        materialization_service: EntityMaterializationService,
    ):
        self._revision_repo = revision_repo
        self._materialization_service = materialization_service

    def resolve_link(
        self,
        entity_id: str,
        link_id: str,
        source_row,
        revision_id: str | None = None,
    ):
        """Resolve a single link for a given source row.

        Returns a single target row for 1:1, a list of target rows for 1:M,
        or None for optional links when the target is not available.
        Raises NotFoundError for required links when the target is missing.
        """
        revision = self._get_revision(entity_id, revision_id)
        link = self._find_link(revision, link_id)
        target_revision = self._revision_repo.get_published(link.target_entity_id)

        if target_revision is None:
            if link.is_optional:
                return None
            raise NotFoundError(f"Target entity '{link.target_entity_id}' for link '{link_id}' is not published")

        source_value = source_row.row_data.get(link.source_property_key)
        if source_value is None:
            if link.is_optional:
                return None
            raise NotFoundError(f"Source row missing value for property '{link.source_property_key}'")

        target_rows = self._materialization_service.get_rows(
            link.target_entity_id, revision_id=target_revision.id, include_tombstones=False
        )

        if link.cardinality == LinkCardinality.ONE_TO_ONE.value:
            result = self._resolve_one_to_one(target_rows, link.target_property_key, source_value)
            if result is None:
                if link.is_optional:
                    return None
                raise NotFoundError(
                    f"No target row found for link '{link_id}' with {link.target_property_key}={source_value}"
                )
            return result
        else:
            results = self._resolve_one_to_many(target_rows, link.target_property_key, source_value)
            if not results:
                if link.is_optional:
                    return None
                raise NotFoundError(
                    f"No target rows found for link '{link_id}' with {link.target_property_key}={source_value}"
                )
            return results

    def resolve_link_batch(
        self,
        entity_id: str,
        link_id: str,
        source_rows: list,
        revision_id: str | None = None,
    ) -> dict:
        """Resolve a link for multiple source rows.

        Returns a dict mapping source_row.row_id -> resolved target row(s).
        """
        results: dict = {}
        for row in source_rows:
            try:
                results[row.row_id] = self.resolve_link(entity_id, link_id, row, revision_id)
            except NotFoundError:
                if not self._find_link(self._get_revision(entity_id, revision_id), link_id).is_optional:
                    raise
                results[row.row_id] = None
        return results

    # ── Internal helpers ─────────────────────────────────────────────────

    def _get_revision(self, entity_id: str, revision_id: str | None) -> "EntityRevision":
        if revision_id:
            revision = self._revision_repo.get(revision_id)
            if revision is None or revision.entity_id != entity_id:
                raise NotFoundError("Revision not found")
            return revision
        published = self._revision_repo.get_published(entity_id)
        if published is None:
            raise NotFoundError("No published revision found for this entity")
        return published

    def _find_link(self, revision, link_id: str) -> EntityLink:
        for raw in revision.links or []:
            link = raw if isinstance(raw, EntityLink) else EntityLink.from_dict(raw)
            if link.link_id == link_id:
                return link
        raise NotFoundError(f"Link '{link_id}' not found in revision")

    def _resolve_one_to_one(self, target_rows, target_property_key: str, value):
        for row in target_rows:
            if row.row_data.get(target_property_key) == value:
                return row
        return None

    def _resolve_one_to_many(self, target_rows, target_property_key: str, value) -> list:
        return [row for row in target_rows if row.row_data.get(target_property_key) == value]
