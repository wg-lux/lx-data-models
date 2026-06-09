from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base import (
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
    from lx_dtypes.models.ledger import (
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
    from lx_dtypes.models.main import (
        DDICTS,
        MODEL_NAMES,
        MODEL_NAMES_LITERAL,
        MODELS,
        MODELS_DJANGO,
    )
    from lx_dtypes.models.meta.SensitiveMeta import (
        SensitiveMeta,
        SensitiveMetaDataDict,
        SensitiveMetaState,
        SensitiveMetaStateDataDict,
    )

_KNOWLEDGE_BASE_EXPORTS = {
    "KB_DDICTS",
    "KB_MODEL_NAMES_LITERAL",
    "KB_MODEL_NAMES_ORDERED",
    "KB_MODELS",
    "KB_MODELS_DJANGO",
    "KnowledgeBaseModelsDjangoLookupType",
    "KnowledgeBaseModelsLookupType",
    "knowledge_base_models_django_lookup",
    "knowledge_base_models_lookup",
}

_LEDGER_EXPORTS = {
    "L_DDICTS",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "L_MODELS",
    "L_MODELS_DJANGO",
    "LedgerModelsDjangoLookupType",
    "LedgerModelsLookupType",
    "ledger_models_django_lookup",
    "ledger_models_lookup",
}

_MAIN_EXPORTS = {
    "DDICTS",
    "MODEL_NAMES",
    "MODEL_NAMES_LITERAL",
    "MODELS",
    "MODELS_DJANGO",
}

_META_EXPORTS = {
    "SensitiveMeta",
    "SensitiveMetaDataDict",
    "SensitiveMetaState",
    "SensitiveMetaStateDataDict",
}


def __getattr__(name: str) -> Any:
    if name in _KNOWLEDGE_BASE_EXPORTS:
        module = import_module("lx_dtypes.models.knowledge_base")
        return getattr(module, name)

    if name in _LEDGER_EXPORTS:
        module = import_module("lx_dtypes.models.ledger")
        return getattr(module, name)

    if name in _MAIN_EXPORTS:
        module = import_module("lx_dtypes.models.main")
        return getattr(module, name)

    if name in _META_EXPORTS:
        module = import_module("lx_dtypes.models.meta.SensitiveMeta")
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    "SensitiveMeta",
    "SensitiveMetaDataDict",
    "SensitiveMetaState",
    "SensitiveMetaStateDataDict",
]
