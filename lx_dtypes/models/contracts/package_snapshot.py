"""Complete, typed and portable persistence of a resolved knowledge base."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Literal, Self, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base.pydantic_main import (
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    knowledge_base_models_lookup,
)
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateLifecycleStatusLiteral,
    ReportTemplateReadinessSummary,
)
from lx_dtypes.utils.parser import camel_to_snake

from .json_types import JsonObject, JsonValue
from .knowledge_base import KnowledgeBaseIdentity
from .study_metadata import StudyMetadata

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


def _semantic_content(value: object, serialized: JsonValue) -> JsonValue:
    """Runtime identifiers and timestamps are not package release identity."""
    if isinstance(value, BaseModel) and isinstance(serialized, dict):
        excluded = (
            {"uuid", "created_at", "source_file"}
            if isinstance(value, AppBaseModel)
            else set()
        )
        if isinstance(value, StudyMetadata):
            # Preserve imports authored before optional analysis or text rules existed.
            for optional in (
                "analysis_definitions",
                "text_extraction",
                "classification_text_extraction",
            ):
                if not getattr(value, optional):
                    excluded.add(optional)
        fields = {
            key: name
            for name, field in type(value).model_fields.items()
            for key in (name, field.serialization_alias, field.alias)
            if key is not None
        }
        return {
            key: _semantic_content(getattr(value, fields.get(key, key)), item)
            for key, item in serialized.items()
            if fields.get(key, key) not in excluded
        }
    if isinstance(value, list) and isinstance(serialized, list):
        return [
            _semantic_content(item, dumped)
            for item, dumped in zip(cast(list[object], value), serialized, strict=True)
        ]
    if isinstance(value, dict) and isinstance(serialized, dict):
        return {
            key: _semantic_content(cast(dict[str, object], value)[key], item)
            for key, item in serialized.items()
        }
    return serialized


def _digest(content: dict[str, object]) -> str:
    typed = dict(content)
    typed["config"] = KnowledgeBaseConfig.model_validate(content["config"])
    typed["module_configs"] = {
        name: KnowledgeBaseConfig.model_validate(config)
        for name, config in cast(dict[str, object], content["module_configs"]).items()
    }
    typed["records"] = PackageSnapshot.validate_records(content["records"])
    normalized = _semantic_content(typed, cast(JsonValue, content))
    encoded = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(encoded.encode()).hexdigest()


class PackageSnapshot(BaseModel):
    """Every runtime record family, validated by its canonical owning model.

    Unlike the frontend graph projection this includes validators, presets,
    reference catalogs and employee lists. Storage paths are intentionally absent.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, ser_json_inf_nan="strings")

    contract_version: Literal["package_snapshot_v1"] = "package_snapshot_v1"
    identity: KnowledgeBaseIdentity
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    config: KnowledgeBaseConfig
    module_configs: dict[str, KnowledgeBaseConfig]
    records: dict[str, list[KB_MODELS]]
    reporting_modules: list[str]
    report_template_lifecycle_status: dict[str, ReportTemplateLifecycleStatusLiteral]

    @field_validator("records", mode="plain")
    @classmethod
    def validate_records(cls, value: object) -> dict[str, list[KB_MODELS]]:
        if not isinstance(value, dict):
            raise ValueError("records must be a model-family mapping")  # noqa: TRY004 - Pydantic must emit ValidationError.
        supplied = cast(dict[str, object], value)
        if set(supplied) != set(KB_MODEL_NAMES_ORDERED):
            raise ValueError(
                "records must contain exactly all registered model families"
            )
        result: dict[str, list[KB_MODELS]] = {}
        for kind, records in supplied.items():
            if not isinstance(records, list):
                raise ValueError(f"{kind} records must be a list")  # noqa: TRY004 - Pydantic must emit ValidationError.
            model = cast(dict[str, type[BaseModel]], knowledge_base_models_lookup)[kind]
            result[kind] = [
                cast(
                    KB_MODELS,
                    model.model_validate(
                        record.model_dump(mode="python", by_alias=True)
                    )
                    if isinstance(record, BaseModel)
                    else model.model_validate_json(json.dumps(record)),
                )
                for record in cast(list[object], records)
            ]
        return result

    @field_serializer("records")
    def serialize_records(
        self, value: dict[str, list[KB_MODELS]]
    ) -> dict[str, list[JsonObject]]:
        return {
            kind: [_record_payload(record) for record in records]
            for kind, records in value.items()
        }

    @model_validator(mode="after")
    def validate_snapshot(self) -> Self:
        if self.config.knowledge_base_identity != self.identity:
            raise ValueError("snapshot config does not match identity")
        expected = {self.config.name, *self.config.modules, *self.config.depends_on}
        if set(self.module_configs) != expected:
            raise ValueError(
                "snapshot requires exact configs for every resolved module"
            )
        if self.module_configs[self.config.name] != self.config:
            raise ValueError("root module config differs from snapshot config")
        if not set(self.reporting_modules).issubset(expected):
            raise ValueError("unknown reporting module")
        for name, config in self.module_configs.items():
            if name != config.name:
                raise ValueError("module config key differs from its name")
            if not {*config.modules, *config.depends_on}.issubset(expected):
                raise ValueError("module config references an unresolved dependency")
            data = config.data
            if data.file or data.dir or data.files or data.dirs:
                raise ValueError("snapshot configs must not contain storage paths")
        for records in self.records.values():
            names = [record.name for record in records]
            if len(names) != len(set(names)):
                raise ValueError("duplicate names in snapshot record family")
            if any(record.kb_module_name not in expected for record in records):
                raise ValueError("record declares an unresolved module")
        if set(self.report_template_lifecycle_status) - {
            record.name for record in self.records["ReportTemplate"]
        }:
            raise ValueError("lifecycle status references an unknown template")
        if self.snapshot_id != _digest(
            self.model_dump(mode="json", exclude={"snapshot_id"})
        ):
            raise ValueError("package snapshot content does not match snapshot_id")
        kb = _restore(self)
        kb.export_core_concepts()
        for name in kb.report_template:
            readiness = ReportTemplateReadinessSummary.model_validate(
                kb.export_report_template_preview(name)["readiness"]
            )
            if (
                kb.get_report_template_lifecycle_status(name) == "published"
                and not readiness.can_publish
            ):
                raise ValueError(f"published template {name!r} is not publishable")
        return self


def _portable_config(config: KnowledgeBaseConfig) -> KnowledgeBaseConfig:
    payload = config.model_dump(mode="python")
    payload["data"] = {"created_at": config.data.created_at}
    return KnowledgeBaseConfig.model_validate(payload)


def _record_payload(record: KB_MODELS) -> JsonObject:
    return cast(JsonObject, json.loads(record.model_dump_json(by_alias=True)))


def build_package_snapshot(kb: KnowledgeBase) -> PackageSnapshot:
    """Capture a loaded KB without reading files or resolving mutable registries."""
    configs = kb._resolved_module_configs or {kb.config.name: kb.config}
    config = _portable_config(kb.config)
    content: dict[str, object] = {
        "contract_version": "package_snapshot_v1",
        "identity": kb.config.knowledge_base_identity.model_dump(mode="json"),
        "config": config.model_dump(mode="json"),
        "module_configs": {
            name: _portable_config(item).model_dump(mode="json")
            for name, item in sorted(configs.items())
        },
        "records": {
            kind: [
                _record_payload(record)
                for record in sorted(
                    cast(
                        dict[str, KB_MODELS], getattr(kb, camel_to_snake(kind))
                    ).values(),
                    key=lambda record: record.name,
                )
            ]
            for kind in sorted(KB_MODEL_NAMES_ORDERED)
        },
        "reporting_modules": sorted(kb._reporting_modules),
        "report_template_lifecycle_status": kb.report_template_lifecycle_status,
    }
    return PackageSnapshot.model_validate({**content, "snapshot_id": _digest(content)})


def restore_package_snapshot(snapshot: PackageSnapshot) -> KnowledgeBase:
    """Restore owning runtime models from a revalidated persistence envelope."""
    snapshot = PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    return _restore(snapshot)


def _restore(snapshot: PackageSnapshot) -> KnowledgeBase:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

    payload: dict[str, object] = {
        "config": snapshot.config,
        "report_template_lifecycle_status": snapshot.report_template_lifecycle_status,
    }
    for kind, records in snapshot.records.items():
        payload[camel_to_snake(kind)] = {
            record.name: record.model_dump(mode="python", by_alias=True)
            for record in records
        }
    kb = KnowledgeBase.model_validate(payload)
    kb._resolved_module_configs = snapshot.module_configs
    kb._reporting_modules = set(snapshot.reporting_modules)
    return kb
