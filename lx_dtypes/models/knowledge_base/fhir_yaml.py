from __future__ import annotations

from collections.abc import Mapping
from itertools import chain
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import NAMESPACE_URL, uuid5

import yaml

from .fhir import (
    FHIR_EXPORT_DOMAINS,
    MEDICAL_FIELD_EXTENSION_PATH,
    extract_fhir_resources,
    import_fhir_terminology,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

FHIRPayload = Mapping[str, Any] | list[Mapping[str, Any]]


def knowledge_base_from_fhir(
    payload: FHIRPayload,
    *,
    module_name: str = "fhir_import",
    version: str | None = None,
    medical_field: str | None = None,
    author: str | None = None,
    language: str | None = None,
    strict: bool = True,
) -> "KnowledgeBase":
    """Create a validated KnowledgeBase directly from FHIR terminology."""
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
    from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig

    imported = import_fhir_terminology(
        payload,
        module_name=module_name,
        identifier_mode="code",
        language=language,
    )
    _add_stable_uuids(imported, module_name=module_name)
    collections = _index_collections(imported)
    _validate_collections(collections, strict=strict)
    config = KnowledgeBaseConfig(
        name=module_name,
        description=f"Knowledge base imported from FHIR as {module_name}.",
        version=version or _fhir_version(payload) or "0.1.0",
        medical_field=medical_field or _fhir_medical_field(payload),
        author=author,
        uuid=_stable_uuid(module_name, "config", module_name),
    )
    return KnowledgeBase.model_validate(
        {
            "config": config,
            "uuid": _stable_uuid(module_name, "knowledge_base", module_name),
            **collections,
        }
    )


def fhir_to_yaml(
    payload: FHIRPayload,
    *,
    module_name: str = "fhir_import",
    version: str | None = None,
    medical_field: str | None = None,
    author: str | None = None,
    language: str | None = None,
    strict: bool = True,
) -> str:
    """Convert FHIR terminology to a loadable, single-file YAML knowledge base."""
    knowledge_base = knowledge_base_from_fhir(
        payload,
        module_name=module_name,
        version=version,
        medical_field=medical_field,
        author=author,
        language=language,
        strict=strict,
    )
    serialized = _yaml_payload(knowledge_base)
    return yaml.safe_dump(serialized, allow_unicode=True, sort_keys=False)


def write_fhir_yaml(
    payload: FHIRPayload,
    output_path: str | Path,
    **options: Any,
) -> Path:
    """Convert FHIR terminology and write a loadable YAML knowledge-base file."""
    path = Path(output_path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(fhir_to_yaml(payload, **options), encoding="utf-8")
    return path


def _index_collections(
    imported: dict[str, Any],
) -> dict[str, dict[str, dict[str, Any]]]:
    return {
        domain: _records_by_name(imported[domain], domain=domain)
        for domain in FHIR_EXPORT_DOMAINS
    }


def _validate_collections(
    collections: Mapping[str, Mapping[str, Any]],
    *,
    strict: bool,
) -> None:
    if strict and not any(collections.values()):
        raise ValueError("FHIR payload contains no supported terminology CodeSystems")


def _records_by_name(
    records: list[dict[str, Any]],
    *,
    domain: str,
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        name = str(record["name"])
        if name in indexed:
            raise ValueError(f"Duplicate {domain} code {name!r} in FHIR payload")
        indexed[name] = record
    return indexed


def _add_stable_uuids(imported: dict[str, Any], *, module_name: str) -> None:
    for domain in FHIR_EXPORT_DOMAINS:
        for record in imported[domain]:
            record.setdefault(
                "uuid",
                _stable_uuid(module_name, domain, str(record["name"])),
            )


def _stable_uuid(module_name: str, domain: str, name: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"lx-kb:{module_name}:{domain}:{name}"))


def _yaml_payload(knowledge_base: "KnowledgeBase") -> dict[str, Any]:
    serialized = knowledge_base.model_dump(
        mode="json",
        exclude_none=True,
        exclude={"report_template_lifecycle_status"},
    )
    return _without_runtime_metadata(serialized)


def _without_runtime_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return _clean_mapping(value)
    if isinstance(value, list):
        return [_without_runtime_metadata(item) for item in value]
    return value


def _clean_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: _without_runtime_metadata(item)
        for key, item in value.items()
        if key not in {"created_at", "source_file"}
    }


def _fhir_version(payload: FHIRPayload) -> str | None:
    versions = (resource.get("version") for resource in extract_fhir_resources(payload))
    return next((str(version) for version in versions if version), None)


def _fhir_medical_field(payload: FHIRPayload) -> str | None:
    extension_groups = (
        resource.get("extension", []) for resource in extract_fhir_resources(payload)
    )
    extensions = chain.from_iterable(extension_groups)
    values = (_medical_field_value(extension) for extension in extensions)
    return next((value for value in values if value), None)


def _medical_field_value(extension: Any) -> str | None:
    if not isinstance(extension, Mapping):
        return None
    if not str(extension.get("url", "")).endswith(MEDICAL_FIELD_EXTENSION_PATH):
        return None
    value = extension.get("valueCode")
    return str(value) if value else None


__all__ = [
    "FHIRPayload",
    "fhir_to_yaml",
    "knowledge_base_from_fhir",
    "write_fhir_yaml",
]
