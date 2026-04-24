from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main import (
        KB_DDICTS,
        KB_MODEL_NAMES_LITERAL,
        KB_MODEL_NAMES_ORDERED,
        KB_MODELS,
        KB_MODELS_DJANGO,
        DEFAULT_FHIR_BASE_URL,
        DEFAULT_FHIR_PUBLISHER,
        FHIR_EXPORT_DOMAINS,
        KnowledgeBaseModelsDjangoLookupType,
        KnowledgeBaseModelsLookupType,
        export_fhir_terminology,
        export_fhir_terminology_bundle,
        import_fhir_terminology,
        knowledge_base_models_django_lookup,
        knowledge_base_models_lookup,
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
    "import_fhir_terminology",
]

_EXPORTED = set(__all__)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTED:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .main import (
        KB_DDICTS,
        KB_MODEL_NAMES_LITERAL,
        KB_MODEL_NAMES_ORDERED,
        KB_MODELS,
        KB_MODELS_DJANGO,
        DEFAULT_FHIR_BASE_URL,
        DEFAULT_FHIR_PUBLISHER,
        FHIR_EXPORT_DOMAINS,
        KnowledgeBaseModelsDjangoLookupType,
        KnowledgeBaseModelsLookupType,
        export_fhir_terminology,
        export_fhir_terminology_bundle,
        import_fhir_terminology,
        knowledge_base_models_django_lookup,
        knowledge_base_models_lookup,
    )

    exports = {
        "KB_DDICTS": KB_DDICTS,
        "KnowledgeBaseModelsLookupType": KnowledgeBaseModelsLookupType,
        "knowledge_base_models_lookup": knowledge_base_models_lookup,
        "KB_MODELS": KB_MODELS,
        "KB_MODEL_NAMES_LITERAL": KB_MODEL_NAMES_LITERAL,
        "KB_MODEL_NAMES_ORDERED": KB_MODEL_NAMES_ORDERED,
        "KnowledgeBaseModelsDjangoLookupType": KnowledgeBaseModelsDjangoLookupType,
        "knowledge_base_models_django_lookup": knowledge_base_models_django_lookup,
        "KB_MODELS_DJANGO": KB_MODELS_DJANGO,
        "DEFAULT_FHIR_BASE_URL": DEFAULT_FHIR_BASE_URL,
        "DEFAULT_FHIR_PUBLISHER": DEFAULT_FHIR_PUBLISHER,
        "FHIR_EXPORT_DOMAINS": FHIR_EXPORT_DOMAINS,
        "export_fhir_terminology": export_fhir_terminology,
        "export_fhir_terminology_bundle": export_fhir_terminology_bundle,
        "import_fhir_terminology": import_fhir_terminology,
    }
    return exports[name]
