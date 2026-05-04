from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

FHIRResource = dict[str, Any]

DEFAULT_FHIR_BASE_URL = "https://wg-lux.de/fhir"
DEFAULT_FHIR_PUBLISHER = "Working Group Lux"
MEDICAL_FIELD_EXTENSION_PATH = "StructureDefinition/lx-medical-field"

COMMON_PROPERTY_DEFINITIONS: list[dict[str, str]] = [
    {
        "code": "tag",
        "uri": f"{DEFAULT_FHIR_BASE_URL}/StructureDefinition/prop-tag",
        "type": "string",
        "description": "Internal LX tag.",
    },
    {
        "code": "kb-module",
        "uri": f"{DEFAULT_FHIR_BASE_URL}/StructureDefinition/prop-kb-module",
        "type": "string",
        "description": "LX knowledge-base module name.",
    },
    {
        "code": "internal-uuid",
        "uri": f"{DEFAULT_FHIR_BASE_URL}/StructureDefinition/prop-internal-uuid",
        "type": "string",
        "description": "Original LX concept UUID.",
    },
]

DOMAIN_CONFIG: dict[str, dict[str, str]] = {
    "examination": {
        "id": "lx-examination-cs",
        "name": "LxExaminationCodeSystem",
        "title": "LX Examination Terminology",
        "description": (
            "Terminology for medical examinations from the LX knowledge base."
        ),
    },
    "finding": {
        "id": "lx-finding-cs",
        "name": "LxFindingCodeSystem",
        "title": "LX Finding Terminology",
        "description": "Terminology for medical findings from the LX knowledge base.",
    },
    "classification_type": {
        "id": "lx-classification-type-cs",
        "name": "LxClassificationTypeCodeSystem",
        "title": "LX Classification Type Terminology",
        "description": (
            "Structural classification types such as score, staging, or grading."
        ),
    },
    "classification": {
        "id": "lx-classification-cs",
        "name": "LxClassificationCodeSystem",
        "title": "LX Classification Terminology",
        "description": "Terminology for LX finding classifications.",
    },
    "classification_choice": {
        "id": "lx-classification-choice-cs",
        "name": "LxClassificationChoiceCodeSystem",
        "title": "LX Classification Choice Terminology",
        "description": "Allowed values for LX classifications.",
    },
    "unit": {
        "id": "lx-unit-cs",
        "name": "LxUnitCodeSystem",
        "title": "LX Internal Unit Terminology",
        "description": "Internal LX representation of units before UCUM mapping.",
    },
}

FHIR_EXPORT_DOMAINS: tuple[str, ...] = tuple(DOMAIN_CONFIG)
_DOMAIN_BY_CODE_SYSTEM_ID = {
    config["id"]: domain for domain, config in DOMAIN_CONFIG.items()
}


def export_fhir_terminology(
    kb: "KnowledgeBase",
    *,
    base_url: str = DEFAULT_FHIR_BASE_URL,
    publisher: str = DEFAULT_FHIR_PUBLISHER,
    status: str = "active",
    medical_field: str | None = None,
) -> dict[str, list[FHIRResource]]:
    """
    Export the core LX terminology domains as FHIR CodeSystem and ValueSet dicts.

    The exporter is intentionally side-effect free: YAML loading, KB validation, and
    runtime finding validation remain owned by the existing KnowledgeBase layer.
    """

    base_url = base_url.rstrip("/")
    version = str(getattr(getattr(kb, "config", None), "version", "0.0.0"))
    medical_field = medical_field or _kb_medical_field(kb)
    resources_by_domain = {
        domain: list(_collection_values(kb, domain)) for domain in FHIR_EXPORT_DOMAINS
    }
    code_by_domain: dict[str, Any] = {
        domain: _code_lookup(resources)
        for domain, resources in resources_by_domain.items()
    }
    code_by_domain["_classification_records"] = {
        str(_read(record, "name")): record
        for record in resources_by_domain["classification"]
    }

    code_systems = [
        _build_code_system(
            domain=domain,
            records=records,
            code_by_domain=code_by_domain,
            base_url=base_url,
            version=version,
            publisher=publisher,
            status=status,
            medical_field=medical_field,
        )
        for domain, records in resources_by_domain.items()
    ]
    value_sets = _build_value_sets(
        resources_by_domain=resources_by_domain,
        code_by_domain=code_by_domain,
        base_url=base_url,
        version=version,
        publisher=publisher,
        status=status,
        medical_field=medical_field,
    )
    return {"code_systems": code_systems, "value_sets": value_sets}


def export_fhir_terminology_bundle(
    kb: "KnowledgeBase",
    *,
    base_url: str = DEFAULT_FHIR_BASE_URL,
    publisher: str = DEFAULT_FHIR_PUBLISHER,
    status: str = "active",
    medical_field: str | None = None,
) -> FHIRResource:
    """Export terminology resources as a FHIR collection Bundle."""

    base_url = base_url.rstrip("/")
    medical_field = medical_field or _kb_medical_field(kb)
    exported = export_fhir_terminology(
        kb,
        base_url=base_url,
        publisher=publisher,
        status=status,
        medical_field=medical_field,
    )
    resources = [*exported["code_systems"], *exported["value_sets"]]
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "fullUrl": resource["url"],
                "resource": resource,
            }
            for resource in resources
        ],
    }
    _attach_medical_field_extension(
        bundle,
        base_url=base_url,
        medical_field=medical_field,
    )
    return bundle


def import_fhir_terminology(
    payload: Mapping[str, Any] | list[Mapping[str, Any]],
    *,
    module_name: str = "fhir_import",
) -> dict[str, Any]:
    """
    Import FHIR CodeSystem resources into KB storage-compatible terminology dicts.

    The result mirrors the concept collection shape used by the existing KB
    adapters: keys such as ``examination`` and ``classification_choice`` contain
    lists of plain dictionaries that can be compared to YAML-derived concepts.
    """

    resources = _extract_fhir_resources(payload)
    code_systems = [
        resource
        for resource in resources
        if resource.get("resourceType") == "CodeSystem"
    ]
    value_sets = [
        resource for resource in resources if resource.get("resourceType") == "ValueSet"
    ]

    code_display_by_domain = _code_display_lookup_by_domain(code_systems)
    imported: dict[str, Any] = {
        "module_name": module_name,
        "examination": [],
        "finding": [],
        "classification_type": [],
        "classification": [],
        "classification_choice": [],
        "unit": [],
    }

    for code_system in code_systems:
        domain = _domain_from_code_system(code_system)
        if domain is None:
            continue
        imported[domain].extend(
            _record_from_concept(
                domain=domain,
                concept=concept,
                code_display_by_domain=code_display_by_domain,
                fallback_module_name=module_name,
            )
            for concept in code_system.get("concept", [])
        )

    _apply_choice_value_sets(imported, value_sets, code_display_by_domain)
    return imported


def _collection_values(kb: "KnowledgeBase", domain: str) -> list[object]:
    collection = getattr(kb, domain, {})
    if isinstance(collection, Mapping):
        return list(collection.values())
    return []


def _kb_medical_field(kb: "KnowledgeBase") -> str | None:
    value = getattr(getattr(kb, "config", None), "medical_field", None)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _medical_field_extension_url(base_url: str) -> str:
    return f"{base_url}/{MEDICAL_FIELD_EXTENSION_PATH}"


def _attach_medical_field_extension(
    resource: FHIRResource,
    *,
    base_url: str,
    medical_field: str | None,
) -> None:
    if not medical_field:
        return
    resource.setdefault("extension", []).append(
        {
            "url": _medical_field_extension_url(base_url),
            "valueCode": medical_field,
        }
    )


def _extract_fhir_resources(
    payload: Mapping[str, Any] | list[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if isinstance(payload, list):
        return payload
    if payload.get("resourceType") == "Bundle":
        return [
            entry["resource"]
            for entry in payload.get("entry", [])
            if isinstance(entry, Mapping) and isinstance(entry.get("resource"), Mapping)
        ]
    if "code_systems" in payload or "value_sets" in payload:
        return [
            *payload.get("code_systems", []),
            *payload.get("value_sets", []),
        ]
    if payload.get("resourceType") in {"CodeSystem", "ValueSet"}:
        return [payload]
    return []


def _read(record: object, field: str, default: object | None = None) -> object | None:
    if isinstance(record, Mapping):
        return cast(object | None, record.get(field, default))
    return getattr(record, field, default)


def _domain_from_code_system(code_system: Mapping[str, Any]) -> str | None:
    resource_id = str(code_system.get("id", ""))
    if resource_id in _DOMAIN_BY_CODE_SYSTEM_ID:
        return _DOMAIN_BY_CODE_SYSTEM_ID[resource_id]

    url = str(code_system.get("url", ""))
    for domain, config in DOMAIN_CONFIG.items():
        if url.endswith(f"/CodeSystem/{config['id']}"):
            return domain
    return None


def _code_display_lookup_by_domain(
    code_systems: list[Mapping[str, Any]],
) -> dict[str, dict[str, str]]:
    lookups: dict[str, dict[str, str]] = {}
    for code_system in code_systems:
        domain = _domain_from_code_system(code_system)
        if domain is None:
            continue
        lookups[domain] = {
            str(concept.get("code")): str(concept.get("display") or concept.get("code"))
            for concept in code_system.get("concept", [])
        }
    return lookups


def _properties_by_code(
    concept: Mapping[str, Any],
) -> dict[str, list[Mapping[str, Any]]]:
    properties: dict[str, list[Mapping[str, Any]]] = {}
    for item in concept.get("property", []):
        if isinstance(item, Mapping):
            properties.setdefault(str(item.get("code")), []).append(item)
    return properties


def _designation_by_language(concept: Mapping[str, Any]) -> dict[str, str]:
    designations: dict[str, str] = {}
    for item in concept.get("designation", []):
        if isinstance(item, Mapping) and item.get("language") and item.get("value"):
            designations[str(item["language"])] = str(item["value"])
    return designations


def _coding_display(
    property_value: Mapping[str, Any],
    *,
    target_domain: str,
    code_display_by_domain: dict[str, dict[str, str]],
) -> str | None:
    coding = property_value.get("valueCoding")
    if not isinstance(coding, Mapping):
        return None
    if coding.get("display"):
        return str(coding["display"])
    code = str(coding.get("code", ""))
    return code_display_by_domain.get(target_domain, {}).get(code, code or None)


def _record_from_concept(
    *,
    domain: str,
    concept: Mapping[str, Any],
    code_display_by_domain: dict[str, dict[str, str]],
    fallback_module_name: str,
) -> dict[str, Any]:
    properties = _properties_by_code(concept)
    designations = _designation_by_language(concept)
    name = str(concept.get("display") or concept.get("code"))
    record: dict[str, Any] = {
        "name": name,
        "name_de": designations.get("de", name),
        "name_en": designations.get("en", name),
        "description": str(concept.get("definition") or "unknown"),
        "uuid": _first_property_value(properties, "internal-uuid", "valueString"),
        "tags": [
            str(item["valueString"])
            for item in properties.get("tag", [])
            if item.get("valueString")
        ],
        "kb_module_name": (
            _first_property_value(properties, "kb-module", "valueString")
            or fallback_module_name
        ),
    }

    if domain == "examination":
        record["findings"] = _relation_names(
            properties,
            property_code="finding",
            target_domain="finding",
            code_display_by_domain=code_display_by_domain,
        )
        record["examination_types"] = []
        record["indications"] = []
    elif domain == "finding":
        record["finding_types"] = []
        record["classifications"] = _relation_names(
            properties,
            property_code="classification",
            target_domain="classification",
            code_display_by_domain=code_display_by_domain,
        )
        record["interventions"] = []
        record["caused_by_interventions"] = []
    elif domain == "classification":
        record["classification_types"] = _relation_names(
            properties,
            property_code="classification-type",
            target_domain="classification_type",
            code_display_by_domain=code_display_by_domain,
        )
        record["classification_choices"] = []
    elif domain == "classification_choice":
        record["classification_choice_descriptors"] = []
    elif domain == "unit":
        record["abbreviation"] = (
            _first_property_value(properties, "unit-abbreviation", "valueString")
            or name
        )
        record["unit_types"] = []

    return {key: value for key, value in record.items() if value is not None}


def _first_property_value(
    properties: dict[str, list[Mapping[str, Any]]],
    code: str,
    value_key: str,
) -> str | None:
    for item in properties.get(code, []):
        value = item.get(value_key)
        if value:
            return str(value)
    return None


def _relation_names(
    properties: dict[str, list[Mapping[str, Any]]],
    *,
    property_code: str,
    target_domain: str,
    code_display_by_domain: dict[str, dict[str, str]],
) -> list[str]:
    names: list[str] = []
    for item in properties.get(property_code, []):
        display = _coding_display(
            item,
            target_domain=target_domain,
            code_display_by_domain=code_display_by_domain,
        )
        if display:
            names.append(display)
    return names


def _apply_choice_value_sets(
    imported: dict[str, Any],
    value_sets: list[Mapping[str, Any]],
    code_display_by_domain: dict[str, dict[str, str]],
) -> None:
    classifications_by_name = {
        str(record["name"]): record for record in imported["classification"]
    }
    for value_set in value_sets:
        value_set_id = str(value_set.get("id", ""))
        prefix = "lx-classification-choice-for-"
        suffix = "-vs"
        if not value_set_id.startswith(prefix) or not value_set_id.endswith(suffix):
            continue
        classification_code = value_set_id[len(prefix) : -len(suffix)]
        classification_name = code_display_by_domain.get("classification", {}).get(
            classification_code,
            classification_code,
        )
        classification = classifications_by_name.get(classification_name)
        if classification is None:
            continue
        choices = _value_set_concepts(value_set, target_domain="classification_choice")
        if choices:
            classification["classification_choices"] = choices


def _value_set_concepts(
    value_set: Mapping[str, Any],
    *,
    target_domain: str,
) -> list[str]:
    names: list[str] = []
    for include in value_set.get("compose", {}).get("include", []):
        if not isinstance(include, Mapping):
            continue
        if not str(include.get("system", "")).endswith(
            f"/CodeSystem/{DOMAIN_CONFIG[target_domain]['id']}"
        ):
            continue
        for concept in include.get("concept", []):
            if isinstance(concept, Mapping):
                names.append(str(concept.get("display") or concept.get("code")))
    return names


def _as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _slug(value: object) -> str:
    text = str(value or "unknown").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "unknown"


def _resource_url(base_url: str, resource_type: str, resource_id: str) -> str:
    return f"{base_url}/{resource_type}/{resource_id}"


def _code_system_url(base_url: str, domain: str) -> str:
    return _resource_url(base_url, "CodeSystem", DOMAIN_CONFIG[domain]["id"])


def _value_set_url(base_url: str, value_set_id: str) -> str:
    return _resource_url(base_url, "ValueSet", value_set_id)


def _property_uri(base_url: str, code: str) -> str:
    return f"{base_url}/StructureDefinition/prop-{code}"


def _code_lookup(records: list[object]) -> dict[str, str]:
    return {
        str(_read(record, "name")): _slug(_read(record, "name")) for record in records
    }


def _common_properties(record: object) -> list[dict[str, str]]:
    properties: list[dict[str, str]] = []
    for tag in _as_list(_read(record, "tags")):
        properties.append({"code": "tag", "valueString": tag})

    kb_module = _read(record, "kb_module_name")
    if kb_module:
        properties.append({"code": "kb-module", "valueString": str(kb_module)})

    uuid = _read(record, "uuid")
    if uuid:
        properties.append({"code": "internal-uuid", "valueString": str(uuid)})

    return properties


def _designation(record: object) -> list[dict[str, str]]:
    designations: list[dict[str, str]] = []
    for language, field in (("de", "name_de"), ("en", "name_en")):
        value = _read(record, field)
        if value and value != "unknown":
            designations.append({"language": language, "value": str(value)})
    return designations


def _coding_property(
    *,
    property_code: str,
    system: str,
    code: str,
    display: str | None = None,
) -> FHIRResource:
    coding: dict[str, str] = {"system": system, "code": code}
    if display:
        coding["display"] = display
    return {"code": property_code, "valueCoding": coding}


def _relation_properties(
    *,
    domain: str,
    record: object,
    code_by_domain: dict[str, Any],
    base_url: str,
) -> list[FHIRResource]:
    properties: list[dict[str, Any]] = []

    if domain == "examination":
        properties.extend(
            _coded_relation_properties(
                names=_as_list(_read(record, "findings")),
                property_code="finding",
                target_domain="finding",
                code_by_domain=code_by_domain,
                base_url=base_url,
            )
        )
    elif domain == "finding":
        properties.extend(
            _coded_relation_properties(
                names=_as_list(_read(record, "classifications")),
                property_code="classification",
                target_domain="classification",
                code_by_domain=code_by_domain,
                base_url=base_url,
            )
        )
    elif domain == "classification":
        properties.extend(
            _coded_relation_properties(
                names=_as_list(_read(record, "classification_types")),
                property_code="classification-type",
                target_domain="classification_type",
                code_by_domain=code_by_domain,
                base_url=base_url,
            )
        )
    elif domain == "classification_choice":
        properties.extend(
            _classification_choice_parent_properties(
                record=record,
                code_by_domain=code_by_domain,
                base_url=base_url,
            )
        )
    elif domain == "unit":
        abbreviation = _read(record, "abbreviation")
        if abbreviation:
            properties.append(
                {"code": "unit-abbreviation", "valueString": str(abbreviation)}
            )

    return properties


def _coded_relation_properties(
    *,
    names: list[str],
    property_code: str,
    target_domain: str,
    code_by_domain: dict[str, Any],
    base_url: str,
) -> list[FHIRResource]:
    target_codes = code_by_domain[target_domain]
    system = _code_system_url(base_url, target_domain)
    properties: list[FHIRResource] = []
    for name in names:
        target_code = target_codes.get(name)
        if target_code is None:
            continue
        properties.append(
            _coding_property(
                property_code=property_code,
                system=system,
                code=target_code,
                display=name,
            )
        )
    return properties


def _classification_choice_parent_properties(
    *,
    record: object,
    code_by_domain: dict[str, Any],
    base_url: str,
) -> list[FHIRResource]:
    properties: list[FHIRResource] = []
    choice_name = str(_read(record, "name"))

    for classification_name, classification_code in code_by_domain[
        "classification"
    ].items():
        classification = code_by_domain["_classification_records"].get(
            classification_name
        )
        choices = (
            _as_list(_read(classification, "classification_choices"))
            if classification
            else []
        )
        if choice_name not in choices:
            continue
        properties.append(
            _coding_property(
                property_code="classification",
                system=_code_system_url(base_url, "classification"),
                code=classification_code,
                display=classification_name,
            )
        )

    return properties


def _property_definitions(domain: str, base_url: str) -> list[dict[str, str]]:
    definitions = [
        {
            **item,
            "uri": item["uri"].replace(DEFAULT_FHIR_BASE_URL, base_url),
        }
        for item in COMMON_PROPERTY_DEFINITIONS
    ]

    relation_definitions: dict[str, list[dict[str, str]]] = {
        "examination": [
            {
                "code": "finding",
                "uri": _property_uri(base_url, "finding"),
                "type": "Coding",
                "description": "Finding allowed for this examination.",
            }
        ],
        "finding": [
            {
                "code": "classification",
                "uri": _property_uri(base_url, "classification"),
                "type": "Coding",
                "description": "Classification allowed for this finding.",
            }
        ],
        "classification": [
            {
                "code": "classification-type",
                "uri": _property_uri(base_url, "classification-type"),
                "type": "Coding",
                "description": "Classification type from lx-classification-type-cs.",
            }
        ],
        "classification_choice": [
            {
                "code": "classification",
                "uri": _property_uri(base_url, "classification"),
                "type": "Coding",
                "description": "Owning classification from lx-classification-cs.",
            }
        ],
        "unit": [
            {
                "code": "unit-abbreviation",
                "uri": _property_uri(base_url, "unit-abbreviation"),
                "type": "string",
                "description": "Internal unit abbreviation before UCUM mapping.",
            }
        ],
    }
    definitions.extend(relation_definitions.get(domain, []))
    return definitions


def _concept(
    *,
    domain: str,
    record: Any,
    code_by_domain: dict[str, Any],
    base_url: str,
) -> dict[str, Any]:
    display = str(_read(record, "name"))
    concept: dict[str, Any] = {
        "code": _slug(display),
        "display": display,
    }
    description = _read(record, "description")
    if description and description != "unknown":
        concept["definition"] = str(description)

    designations = _designation(record)
    if designations:
        concept["designation"] = designations

    properties = [
        *_common_properties(record),
        *_relation_properties(
            domain=domain,
            record=record,
            code_by_domain=code_by_domain,
            base_url=base_url,
        ),
    ]
    if properties:
        concept["property"] = properties

    return concept


def _build_code_system(
    *,
    domain: str,
    records: list[object],
    code_by_domain: dict[str, Any],
    base_url: str,
    version: str,
    publisher: str,
    status: str,
    medical_field: str | None,
) -> FHIRResource:
    config = DOMAIN_CONFIG[domain]
    resource = {
        "resourceType": "CodeSystem",
        "id": config["id"],
        "url": _code_system_url(base_url, domain),
        "version": version,
        "name": config["name"],
        "title": config["title"],
        "status": status,
        "experimental": False,
        "date": date.today().isoformat(),
        "publisher": publisher,
        "description": config["description"],
        "caseSensitive": True,
        "content": "complete",
        "property": _property_definitions(domain, base_url),
        "concept": [
            _concept(
                domain=domain,
                record=record,
                code_by_domain=code_by_domain,
                base_url=base_url,
            )
            for record in records
        ],
    }
    _attach_medical_field_extension(
        resource,
        base_url=base_url,
        medical_field=medical_field,
    )
    return resource


def _concept_includes(records: list[object]) -> list[dict[str, str]]:
    return [
        {
            "code": _slug(_read(record, "name")),
            "display": str(_read(record, "name")),
        }
        for record in records
    ]


def _base_value_set(
    *,
    value_set_id: str,
    system: str,
    concepts: list[dict[str, str]],
    base_url: str,
    version: str,
    publisher: str,
    status: str,
    medical_field: str | None,
    title: str,
    name: str,
    description: str,
) -> FHIRResource:
    resource = {
        "resourceType": "ValueSet",
        "id": value_set_id,
        "url": _value_set_url(base_url, value_set_id),
        "version": version,
        "name": name,
        "title": title,
        "status": status,
        "experimental": False,
        "date": date.today().isoformat(),
        "publisher": publisher,
        "description": description,
        "compose": {
            "include": [
                {
                    "system": system,
                    "concept": concepts,
                }
            ]
        },
    }
    _attach_medical_field_extension(
        resource,
        base_url=base_url,
        medical_field=medical_field,
    )
    return resource


def _build_value_sets(
    *,
    resources_by_domain: dict[str, list[object]],
    code_by_domain: dict[str, Any],
    base_url: str,
    version: str,
    publisher: str,
    status: str,
    medical_field: str | None,
) -> list[FHIRResource]:
    value_sets: list[FHIRResource] = []
    for domain, records in resources_by_domain.items():
        config = DOMAIN_CONFIG[domain]
        value_set_id = config["id"].replace("-cs", "-vs")
        value_sets.append(
            _base_value_set(
                value_set_id=value_set_id,
                system=_code_system_url(base_url, domain),
                concepts=_concept_includes(records),
                base_url=base_url,
                version=version,
                publisher=publisher,
                status=status,
                medical_field=medical_field,
                title=config["title"].replace("Terminology", "ValueSet"),
                name=config["name"].replace("CodeSystem", "ValueSet"),
                description=f"All concepts from {config['title']}.",
            )
        )

    classifications = resources_by_domain["classification"]
    choices = resources_by_domain["classification_choice"]
    choice_by_name = {str(_read(choice, "name")): choice for choice in choices}
    for classification in classifications:
        classification_name = str(_read(classification, "name"))
        included_choices = [
            choice_by_name[choice_name]
            for choice_name in _as_list(_read(classification, "classification_choices"))
            if choice_name in choice_by_name
        ]
        if not included_choices:
            continue
        classification_code = code_by_domain["classification"].get(
            classification_name, _slug(classification_name)
        )
        value_set_id = f"lx-classification-choice-for-{classification_code}-vs"
        value_sets.append(
            _base_value_set(
                value_set_id=value_set_id,
                system=_code_system_url(base_url, "classification_choice"),
                concepts=_concept_includes(included_choices),
                base_url=base_url,
                version=version,
                publisher=publisher,
                status=status,
                medical_field=medical_field,
                title=f"LX choices for {classification_name}",
                name=f"LxClassificationChoiceFor{_pascal(classification_code)}ValueSet",
                description=(
                    f"Allowed choices for classification {classification_name}."
                ),
            )
        )

    return value_sets


def _pascal(value: str) -> str:
    return "".join(
        part.capitalize() for part in re.split(r"[^a-zA-Z0-9]+", value) if part
    )


__all__ = [
    "DEFAULT_FHIR_BASE_URL",
    "DEFAULT_FHIR_PUBLISHER",
    "FHIR_EXPORT_DOMAINS",
    "export_fhir_terminology",
    "export_fhir_terminology_bundle",
    "import_fhir_terminology",
]
