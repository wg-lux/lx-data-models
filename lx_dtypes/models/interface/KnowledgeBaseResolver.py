"""Resolve, load, and cache knowledge bases by ``module@version`` identity.

Two resolution modes exist:

* **Registry-backed**: when ``LX_DTYPES_KB_REGISTRY`` is set (as a Django
  setting or environment variable), every load must name an exact version and
  the registry maps ``(module, version)`` to input directories or a verified
  packaged provider.
* **Unversioned development loads**: without a registry, a load without a
  version reads from explicit ``input_dirs`` or the packaged data root.

Resolved identities are checked against the loaded module configuration so a
misconfigured registry fails instead of serving different terminology.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping, Sequence
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    RELEASE_GUIDE,
    PackagedKnowledgeBaseIntegrityError,
    PackagedKnowledgeBaseResourceError,
    get_packaged_knowledge_base,
    registered_digest_remediation,
)
from lx_dtypes.models.interface.data_roots import (
    default_data_roots,
    resolve_default_data_root,
)
from lx_dtypes.models.interface.DataLoader import (
    AmbiguousModuleConfigError,
    DataLoader,
    ModuleConfigNotFoundError,
)
from lx_dtypes.models.interface.remote_data_roots import (
    RemoteDataRootError,
    is_remote_data_root,
    resolve_remote_data_root,
)
from lx_dtypes.models.interface.remote_data_roots import (
    normalize_registry_input as normalize_data_root_input,
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
    from django.core.exceptions import ImproperlyConfigured

    configured_path = ""
    try:
        from django.conf import settings

        configured_path = str(getattr(settings, "LX_DTYPES_KB_REGISTRY", "")).strip()
    except ImproperlyConfigured:
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
            f"{descriptor.content_sha256}.\n"
            + registered_digest_remediation(module_name, version)
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


def _load_registry() -> dict[tuple[str, str], tuple[str, ...]]:
    registry_path = _get_registry_path()
    if registry_path is None:
        return {}
    if not registry_path.exists():
        raise KnowledgeBaseRegistryError(
            f"Configured knowledge-base registry does not exist: {registry_path}"
        )

    try:
        payload_bytes = registry_path.read_bytes()
    except OSError as exc:
        raise KnowledgeBaseRegistryError(
            f"Configured knowledge-base registry could not be read: {registry_path}"
        ) from exc
    content_sha256 = sha256(payload_bytes).hexdigest()
    return _load_registry_payload_cached(
        str(registry_path),
        content_sha256,
        payload_bytes,
    )


@lru_cache(maxsize=8)
def _load_registry_payload_cached(
    registry_path: str,
    content_sha256: str,
    payload_bytes: bytes,
) -> dict[tuple[str, str], tuple[str, ...]]:
    # The digest is only part of the lru_cache key: editing the registry file
    # changes the digest and forces a re-parse even though the path is equal.
    del content_sha256
    try:
        raw_payload = json.loads(
            payload_bytes,
            object_pairs_hook=_reject_duplicate_json_object_keys,
        )
    except KnowledgeBaseRegistryError:
        raise
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KnowledgeBaseRegistryError(
            f"Knowledge-base registry is not valid JSON: {registry_path}"
        ) from exc
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


def _reject_duplicate_json_object_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise KnowledgeBaseRegistryError(
                f"Knowledge-base registry contains duplicate JSON key: {key!r}."
            )
        result[key] = value
    return result


def resolve_versioned_input_dirs(
    module_name: str,
    version: str,
) -> tuple[Path, ...]:
    """Look up the input directories registered for ``module_name@version``.

    Remote data roots in the registry are materialized to local paths.

    Raises:
        KnowledgeBaseVersionNotFoundError: If the registry has no such entry.
        KnowledgeBaseRegistryError: If the registry is missing or malformed.
    """
    registry = _load_registry()
    resolved = registry.get((module_name, version))
    if resolved is None:
        available = sorted(
            registered_version
            for registered_module, registered_version in registry
            if registered_module == module_name
        )
        available_text = (
            "Registered versions of this module: " + ", ".join(available) + "."
            if available
            else "The registry has no version of this module."
        )
        raise KnowledgeBaseVersionNotFoundError(
            "Knowledge-base version not provisioned locally for "
            f"module '{module_name}' and version '{version}'. {available_text}\n"
            "Register the exact release, for example with `lx-dtypes-kb-registry "
            f"add <registry.json> --module {module_name} --version {version} "
            "--input-dir <release-root>`, or `lx-dtypes-kb-registry bootstrap` for "
            f"packaged releases. See {RELEASE_GUIDE}."
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
    # Unversioned loads are a development convenience. Once a registry is
    # configured, an exact identity is mandatory so hosts cannot silently load
    # a different terminology version than the one they recorded.
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

    # Versioned loads never fall back to the packaged data root: the version
    # must be provisioned explicitly so deployments are reproducible.
    if _get_registry_path() is not None:
        resolved_input_dirs = resolve_versioned_input_dirs(module_name, version)
    else:
        raise KnowledgeBaseRegistryError(
            "Versioned knowledge-base resolution requires LX_DTYPES_KB_REGISTRY "
            "or explicit input_dirs; packaged data roots are not an implicit runtime fallback."
        )
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
            f"requested identity '{module_name}@{version}'.\n"
            f"The input directories {[str(path) for path in input_dirs]} contain "
            f"config.yaml declaring version '{module_config.version}' "
            f"(source: {module_config.source_file}). Point the registry entry or "
            f"input_dirs at the directory of the '{module_name}@{version}' release. "
            "If that config.yaml was edited to bump its version, also retain the "
            "previous release and update the catalog; see "
            f"{RELEASE_GUIDE}."
        )


@lru_cache(maxsize=64)
def _load_module_config_cached(
    module_name: str,
    input_dir_strings: tuple[str, ...],
) -> KnowledgeBaseConfig:
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
    kb = loader.load_knowledge_base(module_name)
    # Runtime loads fail closed; draft previews and package linting load through
    # DataLoader directly and keep their source-located readiness diagnostics.
    unresolved = kb.unresolved_template_validator_references()
    if unresolved:
        raise ValueError(
            "Published report template validators must resolve within the package "
            "and its dependency closure: "
            + "; ".join(
                f"template '{template}' references missing {model} '{name}'"
                for template, model, name in unresolved
            )
            + ".\nDefine each missing validator in this package or in a module "
            "listed in its `depends_on`, correct the name, or keep the template in "
            "draft lifecycle status until its validators exist. Run "
            "`uv run python scripts/lint_kb_yaml.py --config <package>/config.yaml` "
            "to see source locations."
        )
    return kb


def load_module_config(
    module_name: str,
    *,
    version: str | None = None,
    input_dirs: Sequence[Path] | None = None,
) -> KnowledgeBaseConfig:
    """Load the module configuration of a knowledge base.

    Args:
        module_name: Knowledge-base module name.
        version: Exact module version. Required when a registry is configured.
        input_dirs: Explicit data directories that override registry lookup.

    Returns:
        The initialized module configuration. Results are cached per resolved
        input directories.

    Raises:
        KnowledgeBaseIdentityRequiredError: If a registry is configured and no
            version was given.
        KnowledgeBaseVersionConflictError: If the resolved artifact reports a
            different ``module@version`` than requested.
    """
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
    """Return the resolved ``(module_name, version)`` of a knowledge base.

    Accepts the same arguments and raises the same errors as
    :func:`load_module_config`.
    """
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
    """Load a knowledge base with its dependency closure.

    Args:
        module_name: Knowledge-base module name.
        version: Exact module version. Required when a registry is configured.
        input_dirs: Explicit data directories that override registry lookup.

    Returns:
        The loaded :class:`~lx_dtypes.models.interface.KnowledgeBase.KnowledgeBase`.
        Results are cached per resolved input directories; call
        :func:`clear_knowledge_base_resolver_caches` after changing the data.

    Raises:
        KnowledgeBaseIdentityRequiredError: If a registry is configured and no
            version was given.
        KnowledgeBaseVersionConflictError: If the resolved artifact reports a
            different identity than requested.
        ValueError: If a published report template references a validator that
            does not exist within the package and its dependencies.
    """
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
    """Clear cached registries, module configurations, and knowledge bases."""
    _load_registry_payload_cached.cache_clear()
    _load_module_config_cached.cache_clear()
    _load_knowledge_base_cached.cache_clear()


__all__ = [
    "AmbiguousModuleConfigError",
    "KnowledgeBaseIdentityRequiredError",
    "KnowledgeBaseRegistryError",
    "KnowledgeBaseVersionConflictError",
    "KnowledgeBaseVersionNotFoundError",
    "ModuleConfigNotFoundError",
    "clear_knowledge_base_resolver_caches",
    "get_knowledge_base_identity",
    "load_knowledge_base",
    "load_module_config",
    "resolve_default_data_root",
    "resolve_registry_entry_inputs",
    "resolve_versioned_input_dirs",
]
