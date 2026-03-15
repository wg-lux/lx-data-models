from __future__ import annotations

from .knowledge_base import (
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
from .ledger import (
    L_DDICTS,
    L_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_ORDERED,
    L_MODELS,
    L_MODELS_DJANGO,
    LedgerModelsDjangoLookupType,
    LedgerModelsLookupType,
    ledger_models_django_lookup,
    ledger_models_lookup,
)
from .main import (
    DDICTS,
    MODEL_NAMES,
    MODEL_NAMES_LITERAL,
    MODELS,
    MODELS_DJANGO,
)

__all__ = [
    "MODEL_NAMES",
    "MODEL_NAMES_LITERAL",
    "MODELS",
    "MODELS_DJANGO",
    "DDICTS",
    "KB_DDICTS",
    "KB_MODELS_DJANGO",
    "KnowledgeBaseModelsLookupType",
    "knowledge_base_models_lookup",
    "KB_MODELS",
    "KB_MODEL_NAMES_LITERAL",
    "KB_MODEL_NAMES_ORDERED",
    "KnowledgeBaseModelsDjangoLookupType",
    "knowledge_base_models_django_lookup",
    "L_DDICTS",
    "LedgerModelsLookupType",
    "L_MODELS",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "L_MODELS_DJANGO",
    "LedgerModelsDjangoLookupType",
    "ledger_models_lookup",
    "ledger_models_django_lookup",
]

# from typing import Any

# _EXPORTED = {
#     "MODEL_NAMES",
#     "ModelsDjangoLookupType",
#     "ModelsLookupType",
#     "models_django_lookup",
#     "models_lookup",
#     "MODEL_NAMES_LITERAL",
#     "get_model_pk_field",
# }


# def __getattr__(name: str) -> Any:
#     if name not in _EXPORTED:
#         raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

#     # Lazy import to avoid importing Django model registry for pydantic-only use cases.
#     from .main import (
#         MODEL_NAMES,
#         MODEL_NAMES_LITERAL,
#         ModelsDjangoLookupType,
#         ModelsLookupType,
#         get_model_pk_field,
#         models_django_lookup,
#         models_lookup,
#     )

#     exports = {
#         "MODEL_NAMES": MODEL_NAMES,
#         "ModelsDjangoLookupType": ModelsDjangoLookupType,
#         "ModelsLookupType": ModelsLookupType,
#         "models_django_lookup": models_django_lookup,
#         "models_lookup": models_lookup,
#         "MODEL_NAMES_LITERAL": MODEL_NAMES_LITERAL,
#         "get_model_pk_field": get_model_pk_field,
#     }
#     return exports[name]


# __all__ = list(_EXPORTED)
