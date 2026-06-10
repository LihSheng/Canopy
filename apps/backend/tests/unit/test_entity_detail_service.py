"""Unit tests for EntityDetailService (Issue 6, Step 3).

Service-layer tests with mocked repositories.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from entity_revision.domain import (
    ComputedProperty,
    EntityLink,
    EntityProperty,
    EntityRevision,
    RevisionStatus,
)

pytestmark = pytest.mark.unit


class TestEntityDetailService:
    def test_builds_detail_with_field_groups(self):
        """EntityDetailService returns field_groups for a revision."""
        from entity_detail.service import EntityDetailService

        rev = EntityRevision(
            id="rev-1",
            entity_id="ent-1",
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="salary",
                    display_name="Salary",
                    semantic_type="number",
                    is_required=False,
                    is_primary_key=False,
                    sort_order=1,
                ),
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="salary * 1.1",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                ),
            ],
        )

        mock_rev_repo = MagicMock()
        mock_mat_repo = MagicMock()
        mock_link_resolver = MagicMock()
        mock_formula_engine = MagicMock()

        service = EntityDetailService(
            revision_repo=mock_rev_repo,
            materialization_repo=mock_mat_repo,
            link_resolver=mock_link_resolver,
            formula_engine=mock_formula_engine,
        )

        groups = service.get_field_groups(rev)
        assert len(groups) == 2
        assert groups[0].field_kind == "base"
        assert groups[0].fields[0].property_key == "salary"
        assert groups[1].field_kind == "computed"
        assert groups[1].fields[0].property_key == "total_comp"

    def test_includes_materialized_preview(self):
        """EntityDetailService returns first 5 materialized rows as preview."""
        from entity_detail.service import EntityDetailService
        from entity_materialization.domain import EntityMaterializedRow

        rows = [
            EntityMaterializedRow(
                id=f"r{i}",
                entity_id="ent-1",
                revision_id="rev-1",
                row_id=f"row-{i}",
                row_data={"salary": 1000 * i},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            )
            for i in range(7)
        ]

        mock_rev_repo = MagicMock()
        mock_mat_repo = MagicMock()
        mock_mat_repo.get_rows.return_value = rows
        mock_link_resolver = MagicMock()
        mock_formula_engine = MagicMock()

        service = EntityDetailService(
            revision_repo=mock_rev_repo,
            materialization_repo=mock_mat_repo,
            link_resolver=mock_link_resolver,
            formula_engine=mock_formula_engine,
        )

        preview = service.get_entity_preview("ent-1", "rev-1")
        assert len(preview) == 5
        assert preview[0]["row_data"]["salary"] == 0
        assert preview[4]["row_data"]["salary"] == 4000

    def test_includes_link_status(self):
        """EntityDetailService returns link_status for each link."""
        from entity_detail.service import EntityDetailService

        rev = EntityRevision(
            id="rev-1",
            entity_id="ent-1",
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            links=[
                EntityLink(
                    link_id="l1",
                    display_name="Department",
                    source_property_key="dept_id",
                    target_entity_id="dept-1",
                    target_property_key="id",
                    cardinality="1:1",
                    is_optional=False,
                    is_active=True,
                ).to_dict(),
            ],
        )

        mock_rev_repo = MagicMock()
        mock_rev_repo.get_published.return_value = EntityRevision(
            id="rev-dept",
            entity_id="dept-1",
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[],
        )
        mock_mat_repo = MagicMock()
        mock_link_resolver = MagicMock()
        mock_link_resolver.resolve_link.return_value = MagicMock()
        mock_formula_engine = MagicMock()

        service = EntityDetailService(
            revision_repo=mock_rev_repo,
            materialization_repo=mock_mat_repo,
            link_resolver=mock_link_resolver,
            formula_engine=mock_formula_engine,
        )

        link_status = service.get_link_status("ent-1", rev)
        assert len(link_status) == 1
        assert link_status[0]["link_id"] == "l1"
        assert link_status[0]["resolvable"] is True

    def test_includes_computed_property_warnings_for_draft(self):
        """EntityDetailService returns computed property warnings for a draft revision."""
        from entity_detail.service import EntityDetailService

        draft = EntityRevision(
            id="rev-draft",
            entity_id="ent-1",
            revision_number=2,
            status=RevisionStatus.DRAFT.value,
            properties=[
                EntityProperty(
                    property_id="p1",
                    property_key="salary",
                    display_name="Salary",
                    semantic_type="number",
                    is_required=False,
                    is_primary_key=False,
                    sort_order=1,
                ),
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="missing_prop * 1.1",
                    formula_type="arithmetic",
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                ),
            ],
        )

        mock_rev_repo = MagicMock()
        mock_mat_repo = MagicMock()
        mock_link_resolver = MagicMock()
        mock_formula_engine = MagicMock()
        mock_formula_engine.extract_property_references.return_value = ["missing_prop"]

        service = EntityDetailService(
            revision_repo=mock_rev_repo,
            materialization_repo=mock_mat_repo,
            link_resolver=mock_link_resolver,
            formula_engine=mock_formula_engine,
        )

        warnings = service.get_computed_property_warnings(draft)
        assert len(warnings) == 1
        assert "missing_prop" in warnings[0]
