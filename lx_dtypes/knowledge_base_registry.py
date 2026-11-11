"""Strict provisioning for versioned knowledge-base registries."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, ValidationError, model_validator

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    PackagedKnowledgeBase,
    PackagedKnowledgeBaseCatalog,
    get_packaged_knowledge_base,
    list_packaged_knowledge_bases,
)
from lx_dtypes.models.interface.remote_data_roots import (
    _atomic_write_file,
    is_remote_data_root,
    resolve_remote_data_root,
)
from lx_dtypes.models.model import DtypesModel, FrozenContractModel, StrictContractModel

DEFAULT_PACKAGED_KNOWLEDGE_BASE = "star_upper_gi"
PACKAGED_KNOWLEDGE_BASE_MODULES = tuple(
    dict.fromkeys(
        descriptor.module_name for descriptor in list_packaged_knowledge_bases()
    )
)

logger = logging.getLogger(__name__)


class RegistryActiveIdentity(DtypesModel):
    """Exact active knowledge-base identity."""

    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class ProviderSource(DtypesModel):
    """Stable package-provider registry source."""

    kind: Literal["provider"] = "provider"
    provider: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class FilesystemSource(DtypesModel):
    """Explicit deployment-owned filesystem registry source."""

    kind: Literal["filesystem"] = "filesystem"
    input_dirs: list[str] = Field(min_length=1)


KnowledgeBaseSource = Annotated[
    ProviderSource | FilesystemSource,
    Field(discriminator="kind"),
]


class RegistryEntry(DtypesModel):
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


class RegistryPayload(DtypesModel):
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


class KnowledgeBaseBootstrapResult(DtypesModel):
    """Successful strict bootstrap result."""

    model_config = ConfigDict(frozen=True)

    registry: Path
    module_name: str
    version: str
    validated: tuple[str, ...] = ()
    reused: tuple[str, ...] = ()


VALIDATION_RECEIPTS_NAME = "validation-receipts.json"


class ValidationReceipt(FrozenContractModel):
    """Proof that one identity validated with these exact inputs and validator."""

    inputs_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    validator: str = Field(min_length=1)
    validated_at: datetime = Field(strict=False)


class ValidationReceipts(StrictContractModel):
    """Persisted next to the registry so unchanged identities skip re-validation."""

    schema_version: Literal["1"] = "1"
    receipts: dict[str, ValidationReceipt] = Field(default_factory=dict)


def validation_receipts_path(registry: Path) -> Path:
    return registry.parent / VALIDATION_RECEIPTS_NAME


def _validator_identity() -> str:
    try:
        return f"lx-dtypes {package_version('lx-dtypes')}"
    except PackageNotFoundError as exc:
        raise RuntimeError(
            "lx-dtypes distribution metadata is required for validation receipts"
        ) from exc


def _read_receipts(path: Path) -> ValidationReceipts:
    if not path.exists():
        return ValidationReceipts()
    try:
        return ValidationReceipts.model_validate_json(path.read_bytes())
    except (OSError, ValidationError):
        # Receipts only ever skip work; an unreadable file means validate everything.
        logger.warning(
            json.dumps(
                {
                    "event": "lx_dtypes.knowledge_base_bootstrap.receipts_ignored",
                    "receipts": str(path),
                },
                sort_keys=True,
            )
        )
        return ValidationReceipts()


def _write_receipts(path: Path, receipts: ValidationReceipts) -> None:
    encoded = (receipts.model_dump_json(indent=2) + "\n").encode("utf-8")
    _atomic_write_file(
        destination=path,
        content=[encoded],
        required_bytes=len(encoded),
        file_mode=0o600,
    )


def _directory_digest(root: Path, cache: dict[Path, str]) -> str:
    resolved = root.resolve()
    if resolved in cache:
        return cache[resolved]
    digest = hashlib.sha256()
    if resolved.is_file():
        files = [resolved]
    else:
        files = sorted(
            path
            for path in resolved.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
    for path in files:
        relative = path.relative_to(resolved).as_posix() if path != resolved else ""
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    cache[resolved] = digest.hexdigest()
    return cache[resolved]


def _inputs_digest(
    registry: Path,
    module_name: str,
    version: str,
    validator: str,
    cache: dict[Path, str],
) -> str | None:
    """Digest of everything validation reads; None when inputs cannot be hashed locally."""
    from lx_dtypes.models.interface.KnowledgeBaseResolver import (
        resolve_registry_entry_inputs,
    )

    entry = read_registry(registry).modules[module_name][version]
    entry_payload = entry.model_dump(mode="json", exclude_none=True)
    inputs = resolve_registry_entry_inputs(module_name, version, entry_payload)
    if any(is_remote_data_root(value) for value in inputs):
        return None
    digest = hashlib.sha256()
    for part in (
        ValidationReceipts().schema_version,
        validator,
        module_name,
        version,
        json.dumps(entry_payload, sort_keys=True),
    ):
        digest.update(part.encode("utf-8") + b"\0")
    for value in inputs:
        path = Path(value)
        if not path.exists():
            # Validation reports the missing input; never skip it.
            return None
        digest.update(_directory_digest(path, cache).encode("ascii") + b"\0")
    return f"sha256:{digest.hexdigest()}"


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


def _is_hydrated_entry(
    registry: Path,
    entry: RegistryEntry,
    descriptor: PackagedKnowledgeBase,
) -> bool:
    """Recognize a published editable copy without replacing its contents."""
    metadata = entry.model_extra or {}
    digest = metadata.get("shipped_tree_sha256")
    if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        return False
    if entry.sources is None or len(entry.sources) != 1:
        return False
    source = entry.sources[0]
    if not isinstance(source, FilesystemSource):
        return False
    tree = registry.parent / "shipped" / digest
    marker = json.loads((tree / "origin.json").read_text(encoding="utf-8"))
    if marker != {"source_sha256": digest, "schema_version": 1}:
        return False
    catalog = PackagedKnowledgeBaseCatalog.model_validate_json(
        (tree / "data" / "catalog.json").read_bytes()
    )
    for original in catalog.knowledge_bases:
        if (original.module_name, original.version) != (
            descriptor.module_name,
            descriptor.version,
        ):
            continue
        # Use the original catalog: upgrades and builder edits need not match
        # today's wheel digest. Full identity/content validation follows below.
        expected_root = (tree / original.resource_root).parent
        expected_roots = {str(expected_root)}
        if expected_root in {
            tree / "data" / "terminology",
            tree / "data" / "report_templates",
        }:
            expected_roots.add(str(tree / "data"))
        return (
            metadata.get("hydrated_from_sha256") == original.content_sha256
            and len(source.input_dirs) == 1
            and source.input_dirs[0] in expected_roots
        )
    return False


def _ensure_packaged_entries(payload: RegistryPayload, registry: Path) -> bool:
    changed = False
    for descriptor in list_packaged_knowledge_bases():
        expected = _packaged_registry_entry(descriptor)
        versions = payload.modules.setdefault(descriptor.module_name, {})
        existing = versions.get(descriptor.version)
        if existing == expected:
            continue
        if existing is not None and _is_hydrated_entry(registry, existing, descriptor):
            continue
        if existing is not None and not _is_replaceable_packaged_entry(existing):
            raise ValueError(
                "immutable knowledge-base identity collision for "
                f"{descriptor.module_name}@{descriptor.version}: the existing "
                "entry is not a recognized packaged provider, hydrated copy, "
                "or installed-wheel source",
            )
        versions[descriptor.version] = expected
        changed = True
    return changed


def _migrate_stale_active_packaged_identity(payload: RegistryPayload) -> bool:
    active = payload.active
    if active is None:
        return False
    try:
        get_packaged_knowledge_base(active.module_name, active.version)
    except LookupError:
        pass
    else:
        # A retained historical release is intentional, not stale active state.
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
    from lx_dtypes.models.interface.DataLoader import DataLoader
    from lx_dtypes.models.interface.KnowledgeBaseResolver import (
        resolve_registry_entry_inputs,
    )

    entry = read_registry(registry).modules[module_name][version]
    inputs = resolve_registry_entry_inputs(
        module_name,
        version,
        entry.model_dump(exclude_none=True),
    )
    # A fresh loader validates current artifacts without mutating process-wide
    # environment variables or reusing mutable runtime resolver caches.
    loader = DataLoader(
        input_dirs=[
            resolve_remote_data_root(value, module_name=module_name)
            if is_remote_data_root(value)
            else Path(value)
            for value in inputs
        ]
    )
    loader.load_module_configs()
    config = loader.get_initialized_config(module_name)
    if config.name != module_name or config.version != version:
        raise ValueError(
            "knowledge-base identity does not match its module config: "
            f"expected {module_name}@{version}, got {config.name}@{config.version}"
        )
    loader.load_knowledge_base(module_name)


def bootstrap_packaged_knowledge_bases(
    registry: Path,
    *,
    default_module: str = DEFAULT_PACKAGED_KNOWLEDGE_BASE,
    verify: bool = False,
) -> KnowledgeBaseBootstrapResult:
    """Provision and validate every packaged knowledge base.

    Existing custom active identities are preserved. Missing active state uses
    ``default_module``. Recognized provider and installed-wheel entries may be
    repaired. Hydrated editable copies are preserved and validated, while
    collisions with unrelated deployment-owned sources fail closed.

    An identity whose registry entry, input files and lx-dtypes version match
    a persisted validation receipt is not loaded again, so repeated boots do
    not re-run full validation. ``verify`` validates every identity regardless.
    """

    registry = registry.expanduser().resolve()
    payload = (
        read_registry(registry) if registry.exists() else RegistryPayload(modules={})
    )
    had_registered_modules = bool(payload.modules)
    changed = _ensure_packaged_entries(payload, registry)

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

    receipts_path = validation_receipts_path(registry)
    receipts = _read_receipts(receipts_path)
    validator = _validator_identity()
    digests: dict[Path, str] = {}
    validated: list[str] = []
    reused: list[str] = []

    def validate(module_name: str, version: str) -> None:
        key = f"{module_name}@{version}"
        digest = _inputs_digest(registry, module_name, version, validator, digests)
        receipt = receipts.receipts.get(key)
        if (
            not verify
            and digest is not None
            and receipt is not None
            and receipt.inputs_digest == digest
            and receipt.validator == validator
        ):
            reused.append(key)
            return
        if receipts.receipts.pop(key, None) is not None:
            # Invalidate durably first: a failed (re)validation must not be skipped next boot.
            _write_receipts(receipts_path, receipts)
        _validate_identity(registry, module_name, version)
        validated.append(key)
        if digest is not None:
            receipts.receipts[key] = ValidationReceipt(
                inputs_digest=digest,
                validator=validator,
                validated_at=datetime.now(UTC),
            )
            # Persist each success so a later failure does not repeat finished work.
            _write_receipts(receipts_path, receipts)

    packaged_identities: set[tuple[str, str]] = set()
    for descriptor in list_packaged_knowledge_bases():
        identity = descriptor.module_name, descriptor.version
        validate(*identity)
        packaged_identities.add(identity)

    module_name, version = read_active_identity(registry)
    if (module_name, version) not in packaged_identities:
        validate(module_name, version)

    logger.info(
        json.dumps(
            {
                "event": "lx_dtypes.knowledge_base_bootstrap.validation",
                "validated": validated,
                "reused": reused,
                "verify": verify,
            },
            sort_keys=True,
        )
    )
    return KnowledgeBaseBootstrapResult(
        registry=registry,
        module_name=module_name,
        version=version,
        validated=tuple(validated),
        reused=tuple(reused),
    )


__all__ = [
    "DEFAULT_PACKAGED_KNOWLEDGE_BASE",
    "PACKAGED_KNOWLEDGE_BASE_MODULES",
    "KnowledgeBaseBootstrapResult",
    "RegistryActiveIdentity",
    "RegistryEntry",
    "RegistryPayload",
    "ValidationReceipt",
    "ValidationReceipts",
    "bootstrap_packaged_knowledge_bases",
    "configured_registry_path",
    "read_active_identity",
    "read_registry",
]
