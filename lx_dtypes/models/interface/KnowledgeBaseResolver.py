from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    PackagedKnowledgeBaseIntegrityError,
    PackagedKnowledgeBaseResourceError,
    get_packaged_knowledge_base,
)
from lx_dtypes.models.interface.DataLoader import (
    AmbiguousModuleConfigError,
    DataLoader,
    ModuleConfigNotFoundError,
)
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


class KnowledgeBaseIdentityRequiredError(KnowledgeBaseRegistryError):
    """Raised when registry-backed loading omits the required module version."""


class KnowledgeBaseVersionConflictError(KnowledgeBaseRegistryError):
    """Raised when registry identity and the resolved artifact disagree."""


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


def _resolve_provider_source(
    raw_source: Mapping[object, object],
    *,
    module_name: str,
    version: str,
) -> str:
    provider = raw_source.get("provider")
    if provider != BUILTIN_KNOWLEDGE_BASE_PROVIDER:
        raise KnowledgeBaseRegistryError(
            f"Unknown knowledge-base provider for {module_name}@{version}: {provider!r}."
        )
    expected_digest = raw_source.get("content_sha256")
    if not isinstance(expected_digest, str):
        raise KnowledgeBaseRegistryError(
            f"Provider source for {module_name}@{version} requires content_sha256."
        )
    try:
        descriptor = get_packaged_knowledge_base(module_name, version)
    except LookupError as exc:
        raise KnowledgeBaseVersionNotFoundError(str(exc)) from exc
    if descriptor.content_sha256 != expected_digest:
        raise KnowledgeBaseVersionConflictError(
            "Registered knowledge-base digest conflicts with the installed provider "
            f"for {module_name}@{version}: expected {expected_digest}, installed "
            f"{descriptor.content_sha256}."
        )
    try:
        return str(descriptor.installed_data_root())
    except PackagedKnowledgeBaseIntegrityError as exc:
        raise KnowledgeBaseVersionConflictError(str(exc)) from exc
    except PackagedKnowledgeBaseResourceError as exc:
        raise KnowledgeBaseRegistryError(str(exc)) from exc


def _coerce_sources(
    raw_sources: object,
    *,
    module_name: str,
    version: str,
) -> tuple[str, ...]:
    if not isinstance(raw_sources, Sequence) or isinstance(raw_sources, (str, bytes)):
        raise KnowledgeBaseRegistryError("Registry sources must be a non-empty list.")
    resolved: list[str] = []
    for raw_source in raw_sources:
        if not isinstance(raw_source, Mapping):
            raise KnowledgeBaseRegistryError("Registry sources must be objects.")
        kind = raw_source.get("kind")
        if kind == "provider":
            resolved.append(
                _resolve_provider_source(
                    raw_source,
                    module_name=module_name,
                    version=version,
                )
            )
        elif kind == "filesystem":
            resolved.extend(
                _coerce_input_dirs(
                    raw_source.get("input_dirs"),
                    module_name=module_name,
                    version=version,
                )
            )
        else:
            raise KnowledgeBaseRegistryError(
                f"Unknown knowledge-base source kind: {kind!r}."
            )
    if not resolved:
        raise KnowledgeBaseRegistryError("Registry sources must not be empty.")
    return tuple(resolved)


def _coerce_input_dirs(
    raw_entry: Any,
    *,
    module_name: str,
    version: str,
) -> tuple[str, ...]:
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
        if "sources" in raw_entry:
            return _coerce_sources(
                raw_entry["sources"],
                module_name=module_name,
                version=version,
            )
        if "input_dirs" in raw_entry:
            return _coerce_input_dirs(
                raw_entry["input_dirs"],
                module_name=module_name,
                version=version,
            )
        for key in ("data_root", "path"):
            if key in raw_entry:
                return _coerce_input_dirs(
                    raw_entry[key],
                    module_name=module_name,
                    version=version,
                )
    raise KnowledgeBaseRegistryError(
        "Registry entries must be a path string, a list of path strings, "
        "or an object containing `sources`, `input_dirs`, `data_root`, or `path`."
    )


def resolve_registry_entry_inputs(
    module_name: str,
    version: str,
    raw_entry: object,
) -> tuple[str, ...]:
    """Resolve one persisted registry entry against the current runtime."""

    return _coerce_input_dirs(
        raw_entry,
        module_name=module_name,
        version=version,
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
            registry[(module_name, version)] = resolve_registry_entry_inputs(
                module_name, version, raw_entry
            )
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
        if input_dirs is not None:
            return tuple(input_dirs)
        if _get_registry_path() is not None:
            raise KnowledgeBaseIdentityRequiredError(
                "A configured knowledge-base registry requires an explicit "
                f"module@version identity for module '{module_name}'."
            )
        return _default_input_dirs()

    if input_dirs is not None:
        resolved_input_dirs = tuple(input_dirs)
        _validate_resolved_identity(module_name, version, resolved_input_dirs)
        return resolved_input_dirs

    if _get_registry_path() is not None:
        resolved_input_dirs = resolve_versioned_input_dirs(module_name, version)
    else:
        resolved_input_dirs = _default_input_dirs()
    _validate_resolved_identity(module_name, version, resolved_input_dirs)
    return resolved_input_dirs


def _validate_resolved_identity(
    module_name: str,
    version: str,
    input_dirs: Sequence[Path],
) -> None:
    module_config = _load_module_config_cached(
        module_name,
        tuple(str(path) for path in input_dirs),
    )
    if module_config.name != module_name or module_config.version != version:
        raise KnowledgeBaseVersionConflictError(
            "Resolved knowledge-base artifact identity "
            f"'{module_config.name}@{module_config.version}' conflicts with "
            f"requested identity '{module_name}@{version}'."
        )


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
    "AmbiguousModuleConfigError",
    "KnowledgeBaseIdentityRequiredError",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionConflictError",
    "KnowledgeBaseVersionNotFoundError",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_registry_entry_inputs",
    "resolve_versioned_input_dirs",
    "ModuleConfigNotFoundError",
]
