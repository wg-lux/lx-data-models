from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonObject, JsonValue


class UploadProvenancePayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    entrypoint: str | None = None
    ingest_mode: str | None = None
    source_system: str | None = None
    content_hash: str | None = None
    source_center_key: str | None = None
    storage_class: str | None = None
    storage_tier: str | None = None
    retention_policy: str | None = None
    hub_mode: bool | None = None
    declared_center_key: str | None = None
    declared_center_name: str | None = None
    resolved_center_key: str | None = None
    watched_path: str | None = None
    file_type: str | None = None
    ingest_variant: str | None = None
    sidecar_path: str | None = None
    sidecar_payload: JsonObject = Field(default_factory=dict)
    watcher_processing_path: str | None = None
    processor_name: str | None = None
    processing_handoff: str | None = None
    llm_job_id: str | None = None
    llm_task_id: str | None = None
    llm_queue: str | None = None
    prediction_model_name: str | None = None
    prediction_task_id: str | None = None
    prediction_history_id: int | None = None
    prediction_queue: str | None = None
    video_import_task_id: str | None = None
    video_import_queue: str | None = None
    stored_upload_path: str | None = None
    quarantined_path: str | None = None
    quarantined_sidecar_path: str | None = None
    media_integrity_status: str | None = None
    media_integrity_reason: str | None = None
    media_integrity_missing_artifacts: list[str] = Field(default_factory=list)
    previous_upload_job_id: str | None = None
    custom_marker: str | None = None

    def as_json(self) -> JsonObject:
        return dict(self.model_dump(mode="python"))

    def with_updates(
        self, updates: Mapping[str, JsonValue | None]
    ) -> UploadProvenancePayload:
        payload = self.as_json()
        for key, value in updates.items():
            if value is not None:
                payload[key] = value
        return parse_upload_provenance_payload(payload)


def parse_upload_provenance_payload(
    payload: Mapping[str, JsonValue] | None,
) -> UploadProvenancePayload:
    return UploadProvenancePayload.model_validate(payload or {})


__all__ = ["UploadProvenancePayload", "parse_upload_provenance_payload"]
