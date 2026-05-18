from __future__ import annotations

import copy
import uuid
from datetime import UTC, datetime

from v3.ingestion.domain import TemplateFamily, TemplateVersion, TemplateVersionState


def next_version_number(existing_versions: list[TemplateVersion]) -> int:
    if not existing_versions:
        return 1
    return max(version.version_number for version in existing_versions) + 1


def create_draft_version(template_id: str, spec_json: dict, existing_versions: list[TemplateVersion]) -> TemplateVersion:
    return TemplateVersion(
        id=str(uuid.uuid4()),
        template_id=template_id,
        version_number=next_version_number(existing_versions),
        state=TemplateVersionState.draft.value,
        spec_json=copy.deepcopy(spec_json or {}),
    )


def clone_version(source: TemplateVersion) -> dict:
    return copy.deepcopy(source.spec_json)


def publish_version(version: TemplateVersion) -> TemplateVersion:
    if version.state == TemplateVersionState.published.value:
        raise ValueError("Template version is already published")
    if not version.spec_json:
        raise ValueError("Cannot publish empty spec")
    version.state = TemplateVersionState.published.value
    version.published_at = datetime.now(UTC)
    return version


def validate_bind(version: TemplateVersion | None) -> None:
    if version is None:
        raise ValueError("Template version not found")
    if version.state != TemplateVersionState.published.value:
        raise ValueError("Only published template versions can be bound")
