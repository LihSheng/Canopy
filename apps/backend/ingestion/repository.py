from __future__ import annotations

from copy import deepcopy

from sqlalchemy.orm import Session

from ingestion.domain import (
    CleanedSnapshot,
    CleaningPipeline,
    CleaningStep,
    LineageEdge,
    LineageGraph,
    LineageNode,
    MappingDecision,
    PublishRecord,
    TemplateFamily,
    TemplateVersion,
    UploadRecord,
    WorkflowState,
)


class IngestionRepository:
    def __init__(self, db: Session):
        self._db = db
        self._uploads: dict[str, UploadRecord] = {}
        self._mapping_decisions: dict[str, list[MappingDecision]] = {}
        self._workflow_state: dict[str, WorkflowState] = {}
        self._template_families: dict[str, TemplateFamily] = {}
        self._template_versions: dict[str, TemplateVersion] = {}
        self._pipelines: dict[str, CleaningPipeline] = {}
        self._pipeline_steps: dict[str, list[CleaningStep]] = {}
        self._snapshots: dict[str, CleanedSnapshot] = {}
        self._lineage_nodes: dict[str, list[LineageNode]] = {}
        self._lineage_edges: dict[str, list[LineageEdge]] = {}
        self._publish_records: dict[str, PublishRecord] = {}

    def save_upload(self, record: UploadRecord) -> UploadRecord:
        self._uploads[record.id] = deepcopy(record)
        return record

    def get_upload(self, upload_id: str) -> UploadRecord | None:
        record = self._uploads.get(upload_id)
        return deepcopy(record) if record else None

    def save_mapping_decisions(self, upload_id: str, decisions: list[MappingDecision]) -> list[MappingDecision]:
        self._mapping_decisions[upload_id] = deepcopy(decisions)
        return decisions

    def get_mapping_decisions(self, upload_id: str) -> list[MappingDecision]:
        return deepcopy(self._mapping_decisions.get(upload_id, []))

    def save_workflow_state(self, state: WorkflowState) -> WorkflowState:
        self._workflow_state[state.upload_id] = deepcopy(state)
        return state

    def get_state(self, upload_id: str) -> WorkflowState | None:
        state = self._workflow_state.get(upload_id)
        return deepcopy(state) if state else None

    def save_template_family(self, family: TemplateFamily) -> TemplateFamily:
        self._template_families[family.id] = deepcopy(family)
        return family

    def save_template_version(self, version: TemplateVersion) -> TemplateVersion:
        self._template_versions[version.id] = deepcopy(version)
        return version

    def get_template_version(self, version_id: str) -> TemplateVersion | None:
        version = self._template_versions.get(version_id)
        return deepcopy(version) if version else None

    def save_cleaning_pipeline(self, pipeline: CleaningPipeline) -> CleaningPipeline:
        self._pipelines[pipeline.id] = deepcopy(pipeline)
        return pipeline

    def save_cleaning_step(self, pipeline_id: str, step: CleaningStep) -> CleaningStep:
        self._pipeline_steps.setdefault(pipeline_id, []).append(deepcopy(step))
        return step

    def save_cleaned_snapshot(self, snapshot: CleanedSnapshot) -> CleanedSnapshot:
        self._snapshots[snapshot.id] = deepcopy(snapshot)
        return snapshot

    def save_lineage_graph(self, upload_id: str, graph: LineageGraph) -> LineageGraph:
        self._lineage_nodes[upload_id] = deepcopy(graph.nodes)
        self._lineage_edges[upload_id] = deepcopy(graph.edges)
        return graph

    def save_publish_record(self, record: PublishRecord) -> PublishRecord:
        self._publish_records[record.id] = deepcopy(record)
        return record

    def get_publish_record(self, publish_id: str) -> PublishRecord | None:
        record = self._publish_records.get(publish_id)
        return deepcopy(record) if record else None

    def get_active_publish(self, upload_id: str) -> PublishRecord | None:
        for record in self._publish_records.values():
            if record.upload_id == upload_id and record.status == "active":
                return deepcopy(record)
        return None

    def list_publish_history(self, upload_id: str) -> list[PublishRecord]:
        records = [deepcopy(record) for record in self._publish_records.values() if record.upload_id == upload_id]
        return sorted(records, key=lambda item: item.created_at, reverse=True)

    def deactivate_publish(self, upload_id: str) -> None:
        for record in self._publish_records.values():
            if record.upload_id == upload_id and record.status == "active":
                record.status = "revoked"
