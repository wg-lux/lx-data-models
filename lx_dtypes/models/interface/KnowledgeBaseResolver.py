from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.data_roots import (
    default_data_roots,
    resolve_default_data_root,
)
from lx_dtypes.models.interface.remote_data_roots import (
    is_remote_data_root,
    normalize_registry_input as normalize_data_root_input,
    RemoteDataRootError,
    resolve_remote_data_root,
)

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig


class KnowledgeBaseVersionNotFoundError(LookupError):
    """
    Raised when a requested knowledge-base version is not provisioned locally.
    """


class KnowledgeBaseRegistryError(ValueError):
    """
    Raised when the configured knowledge-base registry is malformed.
    """


def _normalize_registry_input(value: str) -> str:
    try:
        return normalize_data_root_input(value)
    except RemoteDataRootError as exc:
        raise KnowledgeBaseRegistryError(str(exc)) from exc


def _default_input_dirs() -> tuple[Path, ...]:
    return default_data_roots()


def _get_registry_path() -> Path | None:
    configured_path = ""
    try:
        from django.conf import settings

        configured_path = str(getattr(settings, "LX_DTYPES_KB_REGISTRY", "")).strip()
    except Exception:
        configured_path = ""

    if not configured_path:
        configured_path = os.getenv("LX_DTYPES_KB_REGISTRY", "").strip()
    if not configured_path:
        return None
    return Path(configured_path).expanduser().resolve()


def _coerce_input_dirs(raw_entry: Any) -> tuple[str, ...]:
    if isinstance(raw_entry, str):
        return (_normalize_registry_input(raw_entry),)
    if isinstance(raw_entry, Sequence) and not isinstance(raw_entry, (str, bytes)):
        resolved_paths: list[str] = []
        for item in raw_entry:
            if not isinstance(item, str):
                raise KnowledgeBaseRegistryError(
                    "Registry input_dirs entries must be strings."
                )
            resolved_paths.append(_normalize_registry_input(item))
        if not resolved_paths:
            raise KnowledgeBaseRegistryError(
                "Registry input_dirs entries must not be empty."
            )
        return tuple(resolved_paths)
    if isinstance(raw_entry, Mapping):
        if "input_dirs" in raw_entry:
            return _coerce_input_dirs(raw_entry["input_dirs"])
        for key in ("data_root", "path"):
            if key in raw_entry:
                return _coerce_input_dirs(raw_entry[key])
    raise KnowledgeBaseRegistryError(
        "Registry entries must be a path string, a list of path strings, "
        "or an object containing `input_dirs`, `data_root`, or `path`."
    )


@lru_cache(maxsize=1)
def _load_registry() -> dict[tuple[str, str], tuple[str, ...]]:
    registry_path = _get_registry_path()
    if registry_path is None:
        return {}
    if not registry_path.exists():
        raise KnowledgeBaseRegistryError(
            f"Configured knowledge-base registry does not exist: {registry_path}"
        )

    raw_payload = json.loads(registry_path.read_text())
    if not isinstance(raw_payload, Mapping):
        raise KnowledgeBaseRegistryError(
            "Knowledge-base registry must be a JSON object."
        )

    raw_modules = raw_payload.get("modules", raw_payload)
    if not isinstance(raw_modules, Mapping):
        raise KnowledgeBaseRegistryError(
            "Knowledge-base registry `modules` entry must be a JSON object."
        )

    registry: dict[tuple[str, str], tuple[str, ...]] = {}
    for module_name, module_versions in raw_modules.items():
        if not isinstance(module_name, str) or not module_name.strip():
            raise KnowledgeBaseRegistryError(
                "Knowledge-base registry module names must be non-empty strings."
            )
        if not isinstance(module_versions, Mapping):
            raise KnowledgeBaseRegistryError(
                "Knowledge-base registry module version map must be a JSON object."
            )
        for version, raw_entry in module_versions.items():
            if not isinstance(version, str) or not version.strip():
                raise KnowledgeBaseRegistryError(
                    "Knowledge-base registry versions must be non-empty strings."
                )
            registry[(module_name, version)] = _coerce_input_dirs(raw_entry)
    return registry


def resolve_versioned_input_dirs(
    module_name: str,
    version: str,
) -> tuple[Path, ...]:
    registry = _load_registry()
    resolved = registry.get((module_name, version))
    if resolved is None:
        raise KnowledgeBaseVersionNotFoundError(
            "Knowledge-base version not provisioned locally for "
            f"module '{module_name}' and version '{version}'."
        )
    return tuple(
        resolve_remote_data_root(path, module_name=module_name)
        if is_remote_data_root(path)
        else Path(path)
        for path in resolved
    )


def _resolve_input_dirs_for_identity(
    module_name: str,
    *,
    version: str | None,
    input_dirs: Sequence[Path] | None,
) -> tuple[Path, ...]:
    if version is None:
        return tuple(input_dirs or _default_input_dirs())

    if input_dirs is not None:
        resolved_input_dirs = tuple(input_dirs)
        module_config = _load_module_config_cached(
            module_name,
            tuple(str(path) for path in resolved_input_dirs),
        )
        if module_config.version != version:
            raise KnowledgeBaseVersionNotFoundError(
                "Knowledge-base version not provisioned locally for "
                f"module '{module_name}' and version '{version}'."
            )
        return resolved_input_dirs

    try:
        return resolve_versioned_input_dirs(module_name, version)
    except KnowledgeBaseVersionNotFoundError:
        if any(key_module == module_name for key_module, _ in _load_registry()):
            raise
        default_input_dirs = _default_input_dirs()
        module_config = _load_module_config_cached(
            module_name,
            tuple(str(path) for path in default_input_dirs),
        )
        if module_config.version != version:
            raise
        return default_input_dirs


@lru_cache(maxsize=64)
def _load_module_config_cached(
    module_name: str,
    input_dir_strings: tuple[str, ...],
) -> "KnowledgeBaseConfig":
    loader = DataLoader(input_dirs=[Path(path) for path in input_dir_strings])
    loader.load_module_configs()
    return loader.get_initialized_config(module_name)


@lru_cache(maxsize=64)
def _load_knowledge_base_cached(
    module_name: str,
    input_dir_strings: tuple[str, ...],
) -> Any:
    loader = DataLoader(input_dirs=[Path(path) for path in input_dir_strings])
    loader.load_module_configs()
    return loader.load_knowledge_base(module_name)


def load_module_config(
    module_name: str,
    *,
    version: str | None = None,
    input_dirs: Sequence[Path] | None = None,
) -> "KnowledgeBaseConfig":
    resolved_input_dirs = _resolve_input_dirs_for_identity(
        module_name,
        version=version,
        input_dirs=input_dirs,
    )
    return _load_module_config_cached(
        module_name,
        tuple(str(path) for path in resolved_input_dirs),
    )


def get_knowledge_base_identity(
    module_name: str,
    *,
    version: str | None = None,
    input_dirs: Sequence[Path] | None = None,
) -> tuple[str, str]:
    if version is not None:
        return module_name, version

    module_config = load_module_config(
        module_name,
        version=version,
        input_dirs=input_dirs,
    )
    return module_config.name, module_config.version


def load_knowledge_base(
    module_name: str,
    *,
    version: str | None = None,
    input_dirs: Sequence[Path] | None = None,
) -> Any:
    resolved_input_dirs = _resolve_input_dirs_for_identity(
        module_name,
        version=version,
        input_dirs=input_dirs,
    )
    return _load_knowledge_base_cached(
        module_name,
        tuple(str(path) for path in resolved_input_dirs),
    )


def clear_knowledge_base_resolver_caches() -> None:
    _load_registry.cache_clear()
    _load_module_config_cached.cache_clear()
    _load_knowledge_base_cached.cache_clear()


__all__ = [
    "clear_knowledge_base_resolver_caches",
    "get_knowledge_base_identity",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionNotFoundError",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_versioned_input_dirs",
]
