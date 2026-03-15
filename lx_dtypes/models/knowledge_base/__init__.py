from __future__ import annotations

# from typing import Any
from .main import (
    KB_DDICTS,
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    KB_MODELS,
    KB_MODELS_DJANGO,
    KnowledgeBaseModelsDjangoLookupType,
    KnowledgeBaseModelsLookupType,
    knowledge_base_models_django_lookup,
    knowledge_base_models_lookup,
)

# _EXPORTED = {
# "KnowledgeBaseModelsLookupType",
# "knowledge_base_models_lookup",
# "KB_MODELS",
# "KB_MODEL_NAMES_LITERAL",
# "KB_MODEL_NAMES_ORDERED",
# "KnowledgeBaseModelsDjangoLookupType",
# "knowledge_base_models_django_lookup",
# "KB_MODELS_DJANGO",
# }


# def __getattr__(name: str) -> Any:
#     if name not in _EXPORTED:
#         raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

#     from .main import (
#         KB_MODEL_NAMES_LITERAL,
#         KB_MODEL_NAMES_ORDERED,
#         KB_MODELS,
#         KB_MODELS_DJANGO,
#         KnowledgeBaseModelsDjangoLookupType,
#         KnowledgeBaseModelsLookupType,
#         knowledge_base_models_django_lookup,
#         knowledge_base_models_lookup,
#     )

#     exports = {
#         "KnowledgeBaseModelsLookupType": KnowledgeBaseModelsLookupType,
#         "knowledge_base_models_lookup": knowledge_base_models_lookup,
#         "KB_MODELS": KB_MODELS,
#         "KB_MODEL_NAMES_LITERAL": KB_MODEL_NAMES_LITERAL,
#         "KB_MODEL_NAMES_ORDERED": KB_MODEL_NAMES_ORDERED,
#         "KnowledgeBaseModelsDjangoLookupType": KnowledgeBaseModelsDjangoLookupType,
#         "knowledge_base_models_django_lookup": knowledge_base_models_django_lookup,
#         "KB_MODELS_DJANGO": KB_MODELS_DJANGO,
#     }
#     return exports[name]


# __all__ = list(_EXPORTED)
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
]
