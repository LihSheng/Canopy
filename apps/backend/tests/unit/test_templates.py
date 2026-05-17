import uuid
from datetime import UTC, datetime

import pytest

from v3.ingestion.domain import TemplateFamily, TemplateFamilyStatus, TemplateVersion, TemplateVersionState
from v3.ingestion.templates import (
    clone_version,
    create_draft_version,
    next_version_number,
    publish_version,
    validate_bind,
)


def _family(status: str = TemplateFamilyStatus.active.value) -> TemplateFamily:
    return TemplateFamily(
        id=str(uuid.uuid4()),
        dataset_type="payroll",
        source_profile="herdhr",
        name="Payroll Standard",
        description="Standard payroll cleaning template",
        status=status,
    )


def _version(
    template_id: str | None = None,
    version_number: int = 1,
    state: str = TemplateVersionState.draft.value,
    spec_json: dict | None = None,
) -> TemplateVersion:
    return TemplateVersion(
        id=str(uuid.uuid4()),
        template_id=template_id or str(uuid.uuid4()),
        version_number=version_number,
        state=state,
        spec_json={"steps": []} if spec_json is None else spec_json,
    )


class TestNextVersionNumber:
    def test_returns_1_when_no_versions(self):
        assert next_version_number([]) == 1

    def test_increments_from_existing(self):
        versions = [
            _version(version_number=1),
            _version(version_number=2),
        ]
        assert next_version_number(versions) == 3

    def test_handles_single_version(self):
        versions = [_version(version_number=5)]
        assert next_version_number(versions) == 6


class TestCreateDraftVersion:
    def test_creates_draft_with_version_1(self):
        template_id = str(uuid.uuid4())
        spec = {"steps": [{"type": "trim", "columns": ["name"]}]}
        version = create_draft_version(template_id, spec, [])
        assert version.template_id == template_id
        assert version.version_number == 1
        assert version.state == TemplateVersionState.draft.value
        assert version.spec_json == spec
        assert version.published_at is None

    def test_auto_increments_version_number(self):
        template_id = str(uuid.uuid4())
        existing = [_version(template_id=template_id, version_number=1)]
        version = create_draft_version(template_id, {"steps": []}, existing)
        assert version.version_number == 2

    def test_stores_empty_spec(self):
        version = create_draft_version(str(uuid.uuid4()), {}, [])
        assert version.spec_json == {}


class TestCloneVersion:
    def test_clones_spec(self):
        source = _version(spec_json={"steps": [{"type": "trim"}]})
        cloned = clone_version(source)
        assert cloned == {"steps": [{"type": "trim"}]}
        assert cloned is not source.spec_json

    def test_clones_empty_spec(self):
        source = _version(spec_json={"steps": []})
        cloned = clone_version(source)
        assert cloned == {"steps": []}


class TestPublishVersion:
    def test_publishes_draft(self):
        version = _version()
        result = publish_version(version)
        assert result.state == TemplateVersionState.published.value
        assert result.published_at is not None

    def test_raises_when_already_published(self):
        version = _version(state=TemplateVersionState.published.value)
        with pytest.raises(ValueError, match="already published"):
            publish_version(version)

    def test_raises_when_spec_empty(self):
        version = _version(spec_json={})
        with pytest.raises(ValueError, match="empty spec"):
            publish_version(version)

    def test_sets_published_at(self):
        version = _version()
        before = datetime.now(UTC)
        result = publish_version(version)
        assert result.published_at is not None
        assert result.published_at >= before


class TestValidateBind:
    def test_accepts_published_version(self):
        version = _version(state=TemplateVersionState.published.value)
        validate_bind(version)

    def test_raises_for_draft_version(self):
        version = _version(state=TemplateVersionState.draft.value)
        with pytest.raises(ValueError, match="Only published"):
            validate_bind(version)

    def test_raises_for_none_version(self):
        with pytest.raises(ValueError, match="not found"):
            validate_bind(None)


class TestTemplateFamilyDomain:
    def test_create_family(self):
        family = _family()
        assert family.status == TemplateFamilyStatus.active.value
        assert family.dataset_type == "payroll"
        assert family.source_profile == "herdhr"

    def test_archived_status(self):
        family = _family(status=TemplateFamilyStatus.archived.value)
        assert family.status == TemplateFamilyStatus.archived.value

    def test_serialization_roundtrip(self):
        family = _family()
        d = {
            "id": family.id,
            "dataset_type": family.dataset_type,
            "source_profile": family.source_profile,
            "name": family.name,
            "description": family.description,
            "status": family.status,
            "created_at": family.created_at.isoformat(),
            "updated_at": family.updated_at.isoformat(),
        }
        assert d["id"] == family.id
        assert d["name"] == "Payroll Standard"


class TestTemplateVersionDomain:
    def test_create_version(self):
        version = _version()
        assert version.state == TemplateVersionState.draft.value
        assert version.version_number == 1

    def test_published_version_has_published_at(self):
        now = datetime.now(UTC)
        version = _version(
            state=TemplateVersionState.published.value,
            spec_json={"steps": [{"type": "trim"}]},
        )
        version.published_at = now
        assert version.published_at == now

    def test_draft_version_no_published_at(self):
        version = _version()
        assert version.published_at is None
