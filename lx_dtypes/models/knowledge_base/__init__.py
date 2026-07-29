from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pydantic_main import (
        KB_DDICTS,
        KB_MODEL_NAMES_LITERAL,
        KB_MODEL_NAMES_ORDERED,
        KB_MODELS,
        KnowledgeBaseModelsLookupType,
        knowledge_base_models_lookup,
    )
    from .main import (
        KB_MODELS_DJANGO,
        DEFAULT_FHIR_BASE_URL,
        DEFAULT_FHIR_PUBLISHER,
        FHIR_EXPORT_DOMAINS,
        KnowledgeBaseModelsDjangoLookupType,
        export_fhir_terminology,
        export_fhir_terminology_bundle,
        fhir_to_yaml,
        import_fhir_terminology,
        knowledge_base_from_fhir,
        knowledge_base_models_django_lookup,
        write_fhir_yaml,
    )

__all__ = [
    "KB_DDICTS",
    "KnowledgeBaseModelsLookupType",
    "knowledge_base_models_lookup",
    "KB_MODELS",
    "KB_MODEL_NAMES_LITERAL",
    "KB_MODEL_NAMES_ORDERED",
    "KnowledgeBaseModelsDjangoLookupType",
    "knowledge_base_models_django_lookup",
    "KB_MODELS_DJANGO",
    "DEFAULT_FHIR_BASE_URL",
    "DEFAULT_FHIR_PUBLISHER",
    "FHIR_EXPORT_DOMAINS",
    "export_fhir_terminology",
    "export_fhir_terminology_bundle",
    "fhir_to_yaml",
    "import_fhir_terminology",
    "knowledge_base_from_fhir",
    "write_fhir_yaml",
]

_EXPORTED = set(__all__)
_PYDANTIC_EXPORTS = {
    "KB_DDICTS",
    "KnowledgeBaseModelsLookupType",
    "knowledge_base_models_lookup",
    "KB_MODELS",
    "KB_MODEL_NAMES_LITERAL",
    "KB_MODEL_NAMES_ORDERED",
}


def __getattr__(name: str) -> Any:
    if name not in _EXPORTED:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    if name in _PYDANTIC_EXPORTS:
        from . import pydantic_main

        return getattr(pydantic_main, name)

    from .main import (
        KB_MODELS_DJANGO,
        DEFAULT_FHIR_BASE_URL,
        DEFAULT_FHIR_PUBLISHER,
        FHIR_EXPORT_DOMAINS,
        KnowledgeBaseModelsDjangoLookupType,
        export_fhir_terminology,
        export_fhir_terminology_bundle,
        fhir_to_yaml,
        import_fhir_terminology,
        knowledge_base_from_fhir,
        knowledge_base_models_django_lookup,
        write_fhir_yaml,
    )

    exports = {
        "KnowledgeBaseModelsDjangoLookupType": KnowledgeBaseModelsDjangoLookupType,
        "knowledge_base_models_django_lookup": knowledge_base_models_django_lookup,
        "KB_MODELS_DJANGO": KB_MODELS_DJANGO,
        "DEFAULT_FHIR_BASE_URL": DEFAULT_FHIR_BASE_URL,
        "DEFAULT_FHIR_PUBLISHER": DEFAULT_FHIR_PUBLISHER,
        "FHIR_EXPORT_DOMAINS": FHIR_EXPORT_DOMAINS,
        "export_fhir_terminology": export_fhir_terminology,
        "export_fhir_terminology_bundle": export_fhir_terminology_bundle,
        "fhir_to_yaml": fhir_to_yaml,
        "import_fhir_terminology": import_fhir_terminology,
        "knowledge_base_from_fhir": knowledge_base_from_fhir,
        "write_fhir_yaml": write_fhir_yaml,
    }
    return exports[name]
