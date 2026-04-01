from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeAlias

from lx_dtypes.serialization import parse_str_list, serialize_str_list

from .core_concepts import (
    CitationCore,
    ClassificationChoiceCore,
    ClassificationChoiceDescriptorCore,
    ClassificationCore,
    CoreConceptCollection,
    ExaminationCore,
    FindingCore,
    FindingTypeCore,
    IndicationCore,
    IndicationTypeCore,
    InformationSourceCore,
    InformationSourceTypeCore,
    InterventionCore,
    InterventionTypeCore,
    UnitCore,
    UnitTypeCore,
)

CoreConceptName: TypeAlias = Literal[
    "classification",
    "classification_choice",
    "classification_choice_descriptor",
    "examination",
    "finding",
    "finding_type",
    "indication",
    "indication_type",
    "intervention",
    "intervention_type",
    "unit",
    "unit_type",
    "information_source",
    "information_source_type",
    "citation",
]

CoreConceptModel: TypeAlias = (
    ClassificationCore
    | ClassificationChoiceCore
    | ClassificationChoiceDescriptorCore
    | ExaminationCore
    | FindingCore
    | FindingTypeCore
    | IndicationCore
    | IndicationTypeCore
    | InterventionCore
    | InterventionTypeCore
    | UnitCore
    | UnitTypeCore
    | InformationSourceCore
    | InformationSourceTypeCore
    | CitationCore
)

_CONCEPT_MODEL_LOOKUP: dict[CoreConceptName, type[CoreConceptModel]] = {
    "classification": ClassificationCore,
    "classification_choice": ClassificationChoiceCore,
    "classification_choice_descriptor": ClassificationChoiceDescriptorCore,
    "examination": ExaminationCore,
    "finding": FindingCore,
    "finding_type": FindingTypeCore,
    "indication": IndicationCore,
    "indication_type": IndicationTypeCore,
    "intervention": InterventionCore,
    "intervention_type": InterventionTypeCore,
    "unit": UnitCore,
    "unit_type": UnitTypeCore,
    "information_source": InformationSourceCore,
    "information_source_type": InformationSourceTypeCore,
    "citation": CitationCore,
}

_LIST_FIELDS: dict[CoreConceptName, list[str]] = {
    "classification": ["classification_choices", "classification_types"],
    "classification_choice": ["classification_choice_descriptors"],
    "classification_choice_descriptor": ["selection_options"],
    "examination": ["findings", "examination_types", "indications"],
    "finding": ["finding_types", "classifications", "interventions"],
    "finding_type": [],
    "indication": ["indication_types", "classifications", "interventions"],
    "indication_type": [],
    "intervention": ["intervention_types"],
    "intervention_type": [],
    "unit": ["unit_types"],
    "unit_type": [],
    "information_source": ["information_source_types"],
    "information_source_type": [],
    "citation": ["keywords"],
}

_DICT_FIELDS: dict[CoreConceptName, list[str]] = {
    "classification": [],
    "classification_choice": [],
    "classification_choice_descriptor": [
        "numeric_distribution_params",
        "selection_default_options",
    ],
    "examination": [],
    "finding": [],
    "finding_type": [],
    "indication": [],
    "indication_type": [],
    "intervention": [],
    "intervention_type": [],
    "unit": [],
    "unit_type": [],
    "information_source": [],
    "information_source_type": [],
    "citation": ["identifiers"],
}

_SCALAR_EXTRA_FIELDS: dict[CoreConceptName, list[str]] = {
    "classification": [],
    "classification_choice": [],
    "classification_choice_descriptor": [
        "classification_choice_descriptor_type",
        "unit",
        "numeric_min",
        "numeric_max",
        "numeric_distribution",
        "text_max_length",
        "default_value_str",
        "default_value_num",
        "default_value_bool",
        "selection_multiple",
        "selection_multiple_n_min",
        "selection_multiple_n_max",
    ],
    "examination": [],
    "finding": [],
    "finding_type": [],
    "indication": [],
    "indication_type": [],
    "intervention": [],
    "intervention_type": [],
    "unit": ["abbreviation"],
    "unit_type": [],
    "information_source": [],
    "information_source_type": [],
    "citation": [
        "citation_key",
        "title",
        "abstract",
        "publication_year",
        "publication_month",
        "journal",
        "publisher",
        "volume",
        "issue",
        "pages",
        "doi",
        "url",
        "entry_type",
        "language",
    ],
}

_KB_FIELDS: dict[CoreConceptName, str] = {
    "classification": "classification",
    "classification_choice": "classification_choice",
    "classification_choice_descriptor": "classification_choice_descriptor",
    "examination": "examination",
    "finding": "finding",
    "finding_type": "finding_type",
    "indication": "indication",
    "indication_type": "indication_type",
    "intervention": "intervention",
    "intervention_type": "intervention_type",
    "unit": "unit",
    "unit_type": "unit_type",
    "information_source": "information_source",
    "information_source_type": "information_source_type",
    "citation": "citation",
}


def _read_value(record: Mapping[str, Any] | Any, field: str) -> Any:
    if isinstance(record, Mapping):
        return record.get(field)
    return getattr(record, field, None)


def _base_payload(record: Mapping[str, Any] | Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": _read_value(record, "id"),
        "name": _read_value(record, "name"),
        "name_de": _read_value(record, "name_de"),
        "name_en": _read_value(record, "name_en"),
        "description": _read_value(record, "description"),
        "uuid": _read_value(record, "uuid"),
        "kb_module_name": _read_value(record, "kb_module_name"),
        "tags": parse_str_list(_read_value(record, "tags")),
    }
    # Canonical payloads should skip absent DB ids rather than emit None.
    if payload["id"] is None:
        payload.pop("id")
    return payload


def record_to_core_concept(
    concept: CoreConceptName,
    record: Mapping[str, Any] | Any,
) -> CoreConceptModel:
    """Convert KB model instance or dict-like storage record into canonical shape."""

    model_cls = _CONCEPT_MODEL_LOOKUP[concept]
    payload = _base_payload(record)

    for field in _LIST_FIELDS[concept]:
        payload[field] = parse_str_list(_read_value(record, field))

    for field in _DICT_FIELDS[concept]:
        value = _read_value(record, field)
        payload[field] = dict(value) if isinstance(value, Mapping) else {}

    for field in _SCALAR_EXTRA_FIELDS[concept]:
        payload[field] = _read_value(record, field)

    return model_cls.model_validate(payload)


def core_concept_to_storage(
    concept: CoreConceptName,
    value: CoreConceptModel | Mapping[str, Any],
) -> dict[str, Any]:
    """Convert canonical concept payload back to storage-compatible representation."""

    model_cls = _CONCEPT_MODEL_LOOKUP[concept]
    model_value = model_cls.model_validate(value)
    payload = model_value.model_dump(mode="python", exclude_none=True)

    payload["tags"] = serialize_str_list(model_value.tags)

    for field in _LIST_FIELDS[concept]:
        payload[field] = serialize_str_list(payload.get(field, []))

    # KB/YAML storage is keyed by semantic names; API-facing numeric ids are optional.
    payload.pop("id", None)

    return payload


def records_to_core_concepts(
    concept: CoreConceptName,
    records: Iterable[Mapping[str, Any] | Any],
) -> list[CoreConceptModel]:
    return [record_to_core_concept(concept, record) for record in records]


def kb_to_core_concepts_payload(kb: Any) -> CoreConceptCollection:
    """Export all supported core KB concepts into canonical cross-layer payload."""

    module_name = getattr(getattr(kb, "config", None), "name", "unknown")

    payload = {
        "module_name": module_name,
    }

    for concept, kb_field in _KB_FIELDS.items():
        entries = getattr(kb, kb_field, {})
        values = entries.values() if isinstance(entries, Mapping) else []
        payload[kb_field] = records_to_core_concepts(concept, values)

    return CoreConceptCollection.model_validate(payload)


def canonical_payload_to_storage(
    payload: CoreConceptCollection | Mapping[str, Any],
) -> dict[str, Any]:
    """Convert canonical payload collections back to storage-compatible records."""

    collection = CoreConceptCollection.model_validate(payload)
    out: dict[str, Any] = {"module_name": collection.module_name}

    for concept, kb_field in _KB_FIELDS.items():
        concept_values = getattr(collection, kb_field)
        out[kb_field] = [
            core_concept_to_storage(concept, value) for value in concept_values
        ]

    return out


__all__ = [
    "CoreConceptName",
    "CoreConceptModel",
    "record_to_core_concept",
    "records_to_core_concepts",
    "core_concept_to_storage",
    "kb_to_core_concepts_payload",
    "canonical_payload_to_storage",
]
