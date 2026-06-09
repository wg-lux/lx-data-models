from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBaseResolver import (
        KnowledgeBaseRegistryError,
        KnowledgeBaseVersionNotFoundError,
        get_knowledge_base_identity,
        load_knowledge_base,
        load_module_config,
        resolve_default_data_root,
        resolve_versioned_input_dirs,
    )
    from lx_dtypes.models.interface.data_roots import default_data_roots
    from lx_dtypes.models.interface.LookupTracker import KnowledgeBaseLookupTracker

_INTERFACE_EXPORTS = {
    "KnowledgeBaseLookupTracker",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionNotFoundError",
    "get_knowledge_base_identity",
    "load_knowledge_base",
    "load_module_config",
    "default_data_roots",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
}


def __getattr__(name: str) -> Any:
    if name == "KnowledgeBaseLookupTracker":
        module = import_module("lx_dtypes.models.interface.LookupTracker")
        return getattr(module, name)

    if name in _INTERFACE_EXPORTS:
        if name == "default_data_roots":
            module = import_module("lx_dtypes.models.interface.data_roots")
            return getattr(module, name)
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
    "default_data_roots",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
]
