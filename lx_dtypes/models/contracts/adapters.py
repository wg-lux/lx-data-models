from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from math import isfinite
from typing import TYPE_CHECKING, Any, Literal, Protocol, cast

from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.serialization import parse_str_list, serialize_str_list

from .core_concepts import (
    CitationCore,
    ClassificationChoiceCore,
    ClassificationChoiceDescriptorCore,
    ClassificationCore,
    ClassificationTypeCore,
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
    KnowledgeBaseExaminationTypeCore,
    UnitCore,
    UnitTypeCore,
)

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.citation.Citation import Citation
    from lx_dtypes.models.knowledge_base.classification.Classification import (
        Classification,
    )
    from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
        ClassificationType,
    )
    from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
        ClassificationChoice,
    )
    from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
        ClassificationChoiceDescriptor,
    )
    from lx_dtypes.models.knowledge_base.examination.Examination import Examination
    from lx_dtypes.models.knowledge_base.examination.ExaminationType import (
        ExaminationType,
    )
    from lx_dtypes.models.knowledge_base.finding._Finding import Finding
    from lx_dtypes.models.knowledge_base.finding._FindingType import FindingType
    from lx_dtypes.models.knowledge_base.indication.Indication import Indication
    from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
    from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
        InformationSource,
    )
    from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
        InformationSourceType,
    )
    from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
    from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
        InterventionType,
    )
    from lx_dtypes.models.knowledge_base.unit.Unit import Unit
    from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType

    type KnowledgeBaseCoreConceptModel = (
        Classification
        | ClassificationChoice
        | ClassificationChoiceDescriptor
        | ClassificationType
        | Examination
        | ExaminationType
        | Finding
        | FindingType
        | Indication
        | IndicationType
        | Intervention
        | InterventionType
        | Unit
        | UnitType
        | InformationSource
        | InformationSourceType
        | Citation
    )
else:
    type KnowledgeBaseCoreConceptModel = object

type CoreConceptName = Literal[
    "classification",
    "classification_choice",
    "classification_choice_descriptor",
    "classification_type",
    "examination",
    "examination_type",
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

type CoreConceptModel = (
    ClassificationCore
    | ClassificationChoiceCore
    | ClassificationChoiceDescriptorCore
    | ClassificationTypeCore
    | ExaminationCore
    | KnowledgeBaseExaminationTypeCore
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

type CoreConceptStorageRecord = Mapping[str, JsonValue] | KnowledgeBaseCoreConceptModel


class SupportsKnowledgeBaseListFields(Protocol):
    @classmethod
    def list_type_fields(cls) -> list[str]: ...


class _KnowledgeBaseConfig(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...


class _KnowledgeBaseSection(Protocol):
    def values(self) -> Iterable[CoreConceptStorageRecord]: ...


class _KnowledgeBaseLike(Protocol):
    @property
    def config(self) -> _KnowledgeBaseConfig | None: ...

    @property
    def classification(self) -> Mapping[str, Any] | None: ...

    @property
    def classification_choice(self) -> Mapping[str, Any] | None: ...

    @property
    def classification_choice_descriptor(self) -> Mapping[str, Any] | None: ...

    @property
    def classification_type(self) -> Mapping[str, Any] | None: ...

    @property
    def examination(self) -> Mapping[str, Any] | None: ...

    @property
    def examination_type(self) -> Mapping[str, Any] | None: ...

    @property
    def finding(self) -> Mapping[str, Any] | None: ...

    @property
    def finding_type(self) -> Mapping[str, Any] | None: ...

    @property
    def indication(self) -> Mapping[str, Any] | None: ...

    @property
    def indication_type(self) -> Mapping[str, Any] | None: ...

    @property
    def intervention(self) -> Mapping[str, Any] | None: ...

    @property
    def intervention_type(self) -> Mapping[str, Any] | None: ...

    @property
    def unit(self) -> Mapping[str, Any] | None: ...

    @property
    def unit_type(self) -> Mapping[str, Any] | None: ...

    @property
    def information_source(self) -> Mapping[str, Any] | None: ...

    @property
    def information_source_type(self) -> Mapping[str, Any] | None: ...

    @property
    def citation(self) -> Mapping[str, Any] | None: ...


_CONCEPT_MODEL_LOOKUP: dict[CoreConceptName, type[CoreConceptModel]] = {
    "classification": ClassificationCore,
    "classification_choice": ClassificationChoiceCore,
    "classification_choice_descriptor": ClassificationChoiceDescriptorCore,
    "classification_type": ClassificationTypeCore,
    "examination": ExaminationCore,
    "examination_type": KnowledgeBaseExaminationTypeCore,
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
    "classification_type": [],
    "examination": ["findings", "examination_types", "indications"],
    "examination_type": [],
    "finding": [
        "finding_types",
        "classifications",
        "interventions",
        "caused_by_interventions",
    ],
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
    "classification_type": [],
    "examination": [],
    "examination_type": [],
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
    "classification_type": [],
    "examination": [],
    "examination_type": [],
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
    "classification_type": "classification_type",
    "examination": "examination",
    "examination_type": "examination_type",
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


def _read_value(record: CoreConceptStorageRecord, field: str) -> JsonValue | None:
    if isinstance(record, Mapping):
        value = record.get(field)
        return value
    value = getattr(record, field, None)
    return cast(JsonValue | None, value)


def _canonical_scalar_value(
    record: CoreConceptStorageRecord, field: str
) -> JsonValue | None:
    """Normalize legacy unbounded KB sentinels at the canonical JSON boundary."""

    value = _read_value(record, field)
    if (
        field in {"numeric_min", "numeric_max"}
        and isinstance(value, float)
        and not isfinite(value)
    ):
        return None
    if field == "unit" and value == "unknown":
        return None
    return value


def _base_payload(record: CoreConceptStorageRecord) -> dict[str, JsonValue]:
    tags_value = _read_value(record, "tags")
    payload: dict[str, JsonValue] = {
        "id": _read_value(record, "id"),
        "name": _read_value(record, "name"),
        "name_de": _read_value(record, "name_de"),
        "name_en": _read_value(record, "name_en"),
        "description": _read_value(record, "description"),
        "uuid": _read_value(record, "uuid"),
        "kb_module_name": _read_value(record, "kb_module_name"),
        "tags": _coerce_json_values(
            parse_str_list(cast(str | Sequence[str] | None, tags_value))
        ),
    }
    # Canonical payloads should skip absent DB ids rather than emit None.
    if payload["id"] is None:
        payload.pop("id")
    return payload


def _record_list_fields(
    concept: CoreConceptName,
    record: CoreConceptStorageRecord,
) -> list[str]:
    if isinstance(record, Mapping):
        return _LIST_FIELDS[concept]

    list_field_provider = cast(SupportsKnowledgeBaseListFields, record.__class__)
    fields = list_field_provider.list_type_fields()
    if not fields:
        return _LIST_FIELDS[concept]

    return [field for field in _LIST_FIELDS[concept] if field in fields]


def record_to_core_concept(
    concept: CoreConceptName,
    record: CoreConceptStorageRecord,
) -> CoreConceptModel:
    """Convert KB model instance or dict-like storage record into canonical shape."""

    model_cls = _CONCEPT_MODEL_LOOKUP[concept]
    payload = _base_payload(record)

    for field in _record_list_fields(concept, record):
        payload[field] = _coerce_json_values(
            parse_str_list(cast(str | Sequence[str] | None, _read_value(record, field)))
        )

    for field in _DICT_FIELDS[concept]:
        value = _read_value(record, field)
        payload[field] = dict(value) if isinstance(value, Mapping) else {}

    for field in _SCALAR_EXTRA_FIELDS[concept]:
        payload[field] = _canonical_scalar_value(record, field)

    return model_cls.model_validate(payload)


def _coerce_json_values(values: list[str]) -> list[JsonValue]:
    return [cast(JsonValue, value) for value in values]


def core_concept_to_storage(
    concept: CoreConceptName,
    value: CoreConceptModel | Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Convert canonical concept payload back to storage-compatible representation."""

    model_cls = _CONCEPT_MODEL_LOOKUP[concept]
    model_value = model_cls.model_validate(value)
    payload = cast(
        dict[str, JsonValue],
        model_value.model_dump(mode="python", exclude_none=True),
    )

    payload["tags"] = serialize_str_list(model_value.tags)

    for field in _LIST_FIELDS[concept]:
        list_value = payload.get(field, [])
        if not isinstance(list_value, (list, tuple)):
            list_value = None
        payload[field] = serialize_str_list(cast(Sequence[str] | None, list_value))

    # KB/YAML storage is keyed by semantic names; API-facing numeric ids are optional.
    payload.pop("id", None)

    return payload


def records_to_core_concepts(
    concept: CoreConceptName,
    records: Iterable[CoreConceptStorageRecord],
) -> list[CoreConceptModel]:
    return [record_to_core_concept(concept, record) for record in records]


def kb_to_core_concepts_payload(kb: _KnowledgeBaseLike) -> CoreConceptCollection:
    """Export all supported core KB concepts into canonical cross-layer payload."""

    config = getattr(kb, "config", None)
    module_name = getattr(config, "name", "unknown")
    module_version = getattr(config, "version", None)

    payload = {
        "module_name": module_name,
    }
    if module_version is not None:
        payload["knowledge_base_module"] = module_name
        payload["knowledge_base_version"] = module_version

    for concept, kb_field in _KB_FIELDS.items():
        entries = getattr(kb, kb_field, {})
        values = entries.values() if isinstance(entries, Mapping) else []
        payload[kb_field] = records_to_core_concepts(
            concept,
            cast(Iterable[CoreConceptStorageRecord], values),
        )

    return CoreConceptCollection.model_validate(payload)


def canonical_payload_to_storage(
    payload: CoreConceptCollection | Mapping[str, JsonValue],
) -> dict[str, JsonValue]:
    """Convert canonical payload collections back to storage-compatible records."""

    collection = CoreConceptCollection.model_validate(payload)
    out: dict[str, JsonValue] = {"module_name": collection.module_name}

    for concept, kb_field in _KB_FIELDS.items():
        concept_values = getattr(collection, kb_field)
        out[kb_field] = [
            core_concept_to_storage(concept, value) for value in concept_values
        ]

    return out


__all__ = [
    "CoreConceptModel",
    "CoreConceptName",
    "canonical_payload_to_storage",
    "core_concept_to_storage",
    "kb_to_core_concepts_payload",
    "record_to_core_concept",
    "records_to_core_concepts",
]
