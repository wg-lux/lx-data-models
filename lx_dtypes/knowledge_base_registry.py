"""Strict provisioning for versioned knowledge-base registries."""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    PackagedKnowledgeBase,
    get_packaged_knowledge_base,
    list_packaged_knowledge_bases,
)
from lx_dtypes.models.interface.remote_data_roots import _atomic_write_file

DEFAULT_PACKAGED_KNOWLEDGE_BASE = "star_upper_gi"
PACKAGED_KNOWLEDGE_BASE_MODULES = tuple(
    descriptor.module_name for descriptor in list_packaged_knowledge_bases()
)

logger = logging.getLogger(__name__)


class RegistryActiveIdentity(BaseModel):
    """Exact active knowledge-base identity."""

    model_config = ConfigDict(extra="forbid")

    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class ProviderSource(BaseModel):
    """Stable package-provider registry source."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["provider"] = "provider"
    provider: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FilesystemSource(BaseModel):
    """Explicit deployment-owned filesystem registry source."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["filesystem"] = "filesystem"
    input_dirs: list[str] = Field(min_length=1)


KnowledgeBaseSource = Annotated[
    ProviderSource | FilesystemSource,
    Field(discriminator="kind"),
]


class RegistryEntry(BaseModel):
    """Validated source entry for one module version."""

    model_config = ConfigDict(extra="allow")

    sources: list[KnowledgeBaseSource] | None = Field(default=None, min_length=1)
    input_dirs: list[str] | None = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> RegistryEntry:
        if (self.sources is None) == (self.input_dirs is None):
            raise ValueError(
                "registry entry requires exactly one source representation",
            )
        return self


class RegistryPayload(BaseModel):
    """Persisted registry schema used by bootstrap provisioning."""

    model_config = ConfigDict(extra="allow")

    modules: dict[str, dict[str, RegistryEntry]]
    active: RegistryActiveIdentity | None = None

    @model_validator(mode="after")
    def validate_active_identity(self) -> RegistryPayload:
        if self.active is None:
            return self
        versions = self.modules.get(self.active.module_name)
        if versions is None or self.active.version not in versions:
            raise ValueError("active knowledge-base identity is not registered")
        return self


class KnowledgeBaseBootstrapResult(BaseModel):
    """Successful strict bootstrap result."""

    model_config = ConfigDict(frozen=True)

    registry: Path
    module_name: str
    version: str


_VALIDATE_IDENTITY_SCRIPT = """
import sys

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    load_knowledge_base,
    load_module_config,
)

module_name, version = sys.argv[1:]
config = load_module_config(module_name, version=version)
if config.name != module_name or config.version != version:
    raise SystemExit(
        "knowledge-base identity does not match its module config: "
        f"expected {module_name}@{version}, got {config.name}@{config.version}"
    )
load_knowledge_base(module_name, version=version)
"""


def configured_registry_path(value: Path | None = None) -> Path:
    """Resolve an explicit path or the governed registry environment value."""

    configured = (
        str(value)
        if value is not None
        else os.environ.get("LX_DTYPES_KB_REGISTRY", "").strip()
    )
    if not configured:
        raise ValueError("--registry or LX_DTYPES_KB_REGISTRY is required")
    return Path(configured).expanduser().resolve()


def read_registry(registry: Path) -> RegistryPayload:
    """Read and validate one existing registry."""

    return RegistryPayload.model_validate_json(registry.read_text(encoding="utf-8"))


def read_active_identity(registry: Path) -> tuple[str, str]:
    """Return the registered active identity or fail explicitly."""

    active = read_registry(registry).active
    if active is None:
        raise ValueError("knowledge-base registry has no active module")
    return active.module_name, active.version


def _packaged_registry_entry(descriptor: PackagedKnowledgeBase) -> RegistryEntry:
    entry: dict[str, object] = {
        "sources": [
            {
                "kind": "provider",
                "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                "content_sha256": descriptor.content_sha256,
            },
        ],
    }
    if descriptor.medical_field:
        entry["medical_field"] = descriptor.medical_field
    return RegistryEntry.model_validate(entry)


def _is_replaceable_packaged_entry(entry: RegistryEntry) -> bool:
    if entry.sources is not None:
        if len(entry.sources) != 1:
            return False
        source = entry.sources[0]
        if isinstance(source, ProviderSource):
            return source.provider == BUILTIN_KNOWLEDGE_BASE_PROVIDER
        paths = tuple(source.input_dirs)
    else:
        paths = tuple(entry.input_dirs or [])

    if len(paths) != 1:
        return False
    normalized_parts = tuple(part.lower() for part in Path(paths[0]).parts)
    return "site-packages" in normalized_parts and normalized_parts[-2:] == (
        "lx_dtypes",
        "data",
    )


def _write_registry(registry: Path, payload: RegistryPayload) -> None:
    encoded = (payload.model_dump_json(indent=2, exclude_none=True) + "\n").encode(
        "utf-8",
    )
    _atomic_write_file(
        destination=registry,
        content=[encoded],
        required_bytes=len(encoded),
        file_mode=0o600,
    )
    logger.info(
        json.dumps(
            {
                "event": "lx_dtypes.knowledge_base_registry.write",
                "status": "ok",
                "registry": str(registry),
            },
            sort_keys=True,
        )
    )


def _ensure_packaged_entries(payload: RegistryPayload) -> bool:
    changed = False
    for requested_module in PACKAGED_KNOWLEDGE_BASE_MODULES:
        descriptor = get_packaged_knowledge_base(requested_module)
        expected = _packaged_registry_entry(descriptor)
        versions = payload.modules.setdefault(descriptor.module_name, {})
        existing = versions.get(descriptor.version)
        if existing == expected:
            continue
        if existing is not None and not _is_replaceable_packaged_entry(existing):
            raise ValueError(
                "immutable knowledge-base identity collision for "
                f"{descriptor.module_name}@{descriptor.version}: the existing "
                "entry is not a recognized packaged provider or installed-wheel "
                "source",
            )
        versions[descriptor.version] = expected
        changed = True
    return changed


def _migrate_stale_active_packaged_identity(payload: RegistryPayload) -> bool:
    active = payload.active
    if active is None:
        return False
    try:
        descriptor = get_packaged_knowledge_base(active.module_name)
    except LookupError:
        return False
    if descriptor.version == active.version:
        return False

    stale_versions = payload.modules[active.module_name]
    stale_entry = stale_versions[active.version]
    if not _is_replaceable_packaged_entry(stale_entry):
        return False
    if descriptor.version not in payload.modules.get(descriptor.module_name, {}):
        raise ValueError(
            "current packaged knowledge-base identity was not registered before "
            "migration",
        )

    del stale_versions[active.version]
    if not stale_versions:
        del payload.modules[active.module_name]
    payload.active = RegistryActiveIdentity(
        module_name=descriptor.module_name,
        version=descriptor.version,
    )
    return True


def _validate_identity(registry: Path, module_name: str, version: str) -> None:
    environment = os.environ.copy()
    environment["LX_DTYPES_KB_REGISTRY"] = str(registry)
    environment.pop("DJANGO_SETTINGS_MODULE", None)
    result = subprocess.run(
        [sys.executable, "-c", _VALIDATE_IDENTITY_SCRIPT, module_name, version],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode == 0:
        return
    detail = result.stderr.strip() or result.stdout.strip()
    raise RuntimeError(
        "knowledge-base identity validation exited with status "
        f"{result.returncode}: {detail}",
    )


def bootstrap_packaged_knowledge_bases(
    registry: Path,
    *,
    default_module: str = DEFAULT_PACKAGED_KNOWLEDGE_BASE,
) -> KnowledgeBaseBootstrapResult:
    """Provision and fully validate every packaged knowledge base.

    Existing custom active identities are preserved. Missing active state uses
    ``default_module``. Recognized provider and installed-wheel entries may be
    repaired, while collisions with deployment-owned sources fail closed.
    """

    registry = registry.expanduser().resolve()
    payload = (
        read_registry(registry) if registry.exists() else RegistryPayload(modules={})
    )
    had_registered_modules = bool(payload.modules)
    changed = _ensure_packaged_entries(payload)

    if payload.active is None:
        descriptor = get_packaged_knowledge_base(default_module)
        payload.active = RegistryActiveIdentity(
            module_name=descriptor.module_name,
            version=descriptor.version,
        )
        changed = True
    elif had_registered_modules:
        changed = _migrate_stale_active_packaged_identity(payload) or changed

    if changed:
        _write_registry(registry, payload)

    packaged_identities: set[tuple[str, str]] = set()
    for requested_module in PACKAGED_KNOWLEDGE_BASE_MODULES:
        descriptor = get_packaged_knowledge_base(requested_module)
        identity = descriptor.module_name, descriptor.version
        _validate_identity(registry, *identity)
        packaged_identities.add(identity)

    module_name, version = read_active_identity(registry)
    if (module_name, version) not in packaged_identities:
        _validate_identity(registry, module_name, version)

    return KnowledgeBaseBootstrapResult(
        registry=registry,
        module_name=module_name,
        version=version,
    )


__all__ = [
    "DEFAULT_PACKAGED_KNOWLEDGE_BASE",
    "PACKAGED_KNOWLEDGE_BASE_MODULES",
    "KnowledgeBaseBootstrapResult",
    "RegistryActiveIdentity",
    "RegistryEntry",
    "RegistryPayload",
    "bootstrap_packaged_knowledge_bases",
    "configured_registry_path",
    "read_active_identity",
    "read_registry",
]
