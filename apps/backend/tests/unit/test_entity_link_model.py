"""Unit tests for the typed EntityLink domain model."""

from entity_revision.domain import EntityLink, LinkCardinality


class TestEntityLinkModel:
    def test_entity_link_construction(self):
        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
            is_optional=False,
            is_active=True,
        )
        assert link.link_id == "link-1"
        assert link.display_name == "Manager"
        assert link.source_property_key == "manager_id"
        assert link.target_entity_id == "target-entity-1"
        assert link.target_property_key == "employee_id"
        assert link.cardinality == "1:1"
        assert link.is_optional is False
        assert link.is_active is True

    def test_is_optional_defaults_to_false(self):
        link = EntityLink(
            link_id="link-2",
            display_name="Department",
            source_property_key="dept_id",
            target_entity_id="target-entity-2",
            target_property_key="id",
            cardinality=LinkCardinality.ONE_TO_MANY.value,
        )
        assert link.is_optional is False

    def test_is_active_defaults_to_true(self):
        link = EntityLink(
            link_id="link-3",
            display_name="Project",
            source_property_key="project_id",
            target_entity_id="target-entity-3",
            target_property_key="id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        assert link.is_active is True

    def test_cardinality_values(self):
        assert LinkCardinality.ONE_TO_ONE.value == "1:1"
        assert LinkCardinality.ONE_TO_MANY.value == "1:M"

    def test_invalid_cardinality_does_not_raise_at_construction(self):
        """Invalid cardinality (e.g., M:M) is accepted at construction;
        validation is deferred to publish time."""
        link = EntityLink(
            link_id="link-4",
            display_name="Bad",
            source_property_key="bad_id",
            target_entity_id="target-4",
            target_property_key="id",
            cardinality="M:M",
        )
        assert link.cardinality == "M:M"

    def test_invalid_cardinality_many_to_one(self):
        """Invalid cardinality 'M:1' is accepted at construction."""
        link = EntityLink(
            link_id="link-5",
            display_name="Bad",
            source_property_key="bad_id",
            target_entity_id="target-5",
            target_property_key="id",
            cardinality="M:1",
        )
        assert link.cardinality == "M:1"

    def test_to_dict(self):
        link = EntityLink(
            link_id="link-6",
            display_name="Team",
            source_property_key="team_id",
            target_entity_id="target-6",
            target_property_key="id",
            cardinality=LinkCardinality.ONE_TO_MANY.value,
            is_optional=True,
        )
        d = link.to_dict()
        assert d["link_id"] == "link-6"
        assert d["cardinality"] == "1:M"
        assert d["is_optional"] is True

    def test_from_dict(self):
        d = {
            "link_id": "link-7",
            "display_name": "Site",
            "source_property_key": "site_id",
            "target_entity_id": "target-7",
            "target_property_key": "id",
            "cardinality": "1:1",
            "is_optional": True,
            "is_active": False,
        }
        link = EntityLink.from_dict(d)
        assert link.link_id == "link-7"
        assert link.cardinality == "1:1"
        assert link.is_optional is True
        assert link.is_active is False

    def test_from_dict_defaults(self):
        d = {
            "link_id": "link-8",
            "display_name": "Unit",
            "source_property_key": "unit_id",
            "target_entity_id": "target-8",
            "target_property_key": "id",
            "cardinality": "1:M",
        }
        link = EntityLink.from_dict(d)
        assert link.is_optional is False
        assert link.is_active is True
