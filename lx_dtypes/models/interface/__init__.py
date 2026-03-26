from __future__ import annotations

from importlib import import_module
from typing import Any

_INTERFACE_EXPORTS = {
    "KnowledgeBaseLookupTracker",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionNotFoundError",
    "get_knowledge_base_identity",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
}


def __getattr__(name: str) -> Any:
    if name == "KnowledgeBaseLookupTracker":
        module = import_module("lx_dtypes.models.interface.LookupTracker")
        return getattr(module, name)

    if name in _INTERFACE_EXPORTS:
        module = import_module("lx_dtypes.models.interface.KnowledgeBaseResolver")
        return getattr(module, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "KnowledgeBaseLookupTracker",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionNotFoundError",
    "get_knowledge_base_identity",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
]
