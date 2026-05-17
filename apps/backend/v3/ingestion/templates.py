import uuid
from datetime import UTC, datetime

from v3.ingestion.domain import TemplateFamily, TemplateFamilyStatus, TemplateVersion, TemplateVersionState


def next_version_number(existing_versions: list[TemplateVersion]) -> int:
    return (max((v.version_number for v in existing_versions), default=0)) + 1


def create_draft_version(template_id: str, spec_json: dict, existing_versions: list[TemplateVersion]) -> TemplateVersion:
    return TemplateVersion(
        id=str(uuid.uuid4()),
        template_id=template_id,
        version_number=next_version_number(existing_versions),
        state=TemplateVersionState.draft.value,
        spec_json=spec_json,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def clone_version(source: TemplateVersion) -> dict:
    return dict(source.spec_json)


def publish_version(version: TemplateVersion) -> TemplateVersion:
    if version.state == TemplateVersionState.published.value:
        raise ValueError("Version is already published")

    if not version.spec_json:
        raise ValueError("Cannot publish a version with an empty spec")

    version.state = TemplateVersionState.published.value
    version.published_at = datetime.now(UTC)
    version.updated_at = datetime.now(UTC)
    return version


def validate_bind(version: TemplateVersion | None) -> None:
    if version is None:
        raise ValueError("Template version not found")
    if version.state != TemplateVersionState.published.value:
        raise ValueError("Only published template versions can be bound to uploads")
