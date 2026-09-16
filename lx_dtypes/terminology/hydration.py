"""Seed an editable, registry-backed copy of the shipped terminology.

The data source is the imported package's data directory, never the process CWD.
Copy into staging, publish a complete tree, then register its concrete paths.
Existing filesystem entries and edited copies are not replaced on later runs.
"""

from __future__ import annotations

import json
import shutil
from hashlib import sha256
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import yaml

from lx_dtypes.knowledge_base_registry import (
    DEFAULT_PACKAGED_KNOWLEDGE_BASE,
    RegistryActiveIdentity,
    RegistryEntry,
)
from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    PackagedKnowledgeBase,
    PackagedKnowledgeBaseCatalog,
    knowledge_base_content_sha256,
)
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)

if TYPE_CHECKING:
    from .terminology_service import TerminologyService


def _module_relative_path(descriptor: PackagedKnowledgeBase) -> Path:
    resource = PurePosixPath(descriptor.resource_root)
    if resource.parts[0] != "data" or len(resource.parts) < 2:
        raise ValueError("Shipped modules must be located beneath lx_dtypes/data")
    relative = Path(*resource.parts[1:])
    if relative.name != descriptor.module_name:
        raise ValueError("Shipped module directory must match its module name")
    return relative


def _files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.relative_to(root).parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Hydration source must not contain symlinks: {path}")
        if path.is_file():
            paths.append(path)
        elif not path.is_dir():
            raise ValueError(f"Unsupported hydration source entry: {path}")
    return paths


def _tree_digest(root: Path) -> str:
    digest = sha256()
    for path in _files(root):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _verify_source(source: Path, descriptor: PackagedKnowledgeBase) -> None:
    module = source / _module_relative_path(descriptor)
    config = yaml.safe_load((module / "config.yaml").read_text(encoding="utf-8"))
    if not isinstance(config, dict) or (config.get("name"), config.get("version")) != (
        descriptor.module_name,
        descriptor.version,
    ):
        raise ValueError("Shipped catalog identity conflicts with config.yaml")
    if knowledge_base_content_sha256(module) != descriptor.content_sha256:
        raise ValueError(
            f"Shipped content digest mismatch: {descriptor.module_name}@{descriptor.version}"
        )


def _needs_copy(
    entry: RegistryEntry | None,
    descriptor: PackagedKnowledgeBase,
    source: Path,
) -> bool:
    if entry is None:
        return True
    raw = entry.model_dump(exclude_none=True)
    sources = raw.get("sources")
    if sources and len(sources) == 1:
        item = sources[0]
        if item.get("kind") == "provider":
            if item.get("provider") != BUILTIN_KNOWLEDGE_BASE_PROVIDER:
                return False
            if item.get("content_sha256") != descriptor.content_sha256:
                raise ValueError(
                    "Registered provider digest conflicts with shipped "
                    f"{descriptor.module_name}@{descriptor.version}"
                )
            return True
        inputs = item.get("input_dirs", [])
    else:
        inputs = raw.get("input_dirs", [])
    # Migrate an explicit path into THIS installation's shipped data only.
    # Other filesystem sources, including older hydrated trees, stay authoritative.
    expected = (source / _module_relative_path(descriptor)).parent
    return (
        len(inputs) == 1
        and Path(inputs[0]).is_absolute()
        and Path(inputs[0]).resolve() == expected
    )


def _publish_copy(source: Path, parent: Path, digest: str) -> tuple[Path, bool]:
    destination = parent / digest
    if parent.is_symlink() or destination.is_symlink():
        raise ValueError("Hydration destination must not be a symlink")
    parent.mkdir(parents=True, exist_ok=True)
    manifest = {"source_sha256": digest, "schema_version": 1}
    if destination.exists():
        # The marker identifies a completed installation, not its current contents:
        # this working copy may have been intentionally edited by the builder.
        marker = json.loads((destination / "origin.json").read_text(encoding="utf-8"))
        if marker != manifest or not (destination / "data").is_dir():
            raise ValueError(
                "Existing hydrated directory is incomplete or unrecognized"
            )
        return destination / "data", False

    with TemporaryDirectory(prefix=".hydrate-", dir=parent) as temporary:
        staging = Path(temporary)
        data = staging / "data"
        data.mkdir()
        for original in _files(source):
            target = data / original.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            # Do not preserve read-only Nix store permissions in the editable copy.
            shutil.copyfile(original, target)
            target.chmod(0o600)
        if _tree_digest(data) != digest:
            raise ValueError(
                "Shipped data changed during hydration; retry with a stable source"
            )
        (staging / "origin.json").write_text(json.dumps(manifest), encoding="utf-8")
        staging.rename(destination)
    return destination / "data", True


def hydrate_registry(
    service: TerminologyService,
    *,
    source_root: Path | None = None,
    default_module: str = DEFAULT_PACKAGED_KNOWLEDGE_BASE,
) -> Path:
    """Copy shipped resources and register their destinations under one writer lock.

    Filesystem sources and active identities are preserved. Missing catalog entries
    are added; matching builtin provider entries are migrated to editable copies.
    Only an initially empty registry receives the default active identity.
    """
    from .terminology_service import TerminologyError

    try:
        source = (
            source_root if source_root is not None else package_data_root()
        ).resolve(strict=True)
        root = service.registry_path.parent.resolve()
        if not source.is_dir():
            raise NotADirectoryError(source)
        if root.is_relative_to(source) or source.is_relative_to(root):
            raise ValueError(
                "Terminology storage and shipped data must not overlap: "
                f"storage={root}, source={source}, "
                f"registry={service.registry_path}. "
                "Set TERMINOLOGY_ROOT to a separate writable directory."
            )
        catalog = PackagedKnowledgeBaseCatalog.model_validate_json(
            (source / "catalog.json").read_bytes()
        )
        with service._lock():
            payload, _ = service._snapshot(allow_missing=True)
            initially_empty = not payload.modules and payload.active is None
            pending = [
                descriptor
                for descriptor in catalog.knowledge_bases
                if _needs_copy(
                    payload.modules.get(descriptor.module_name, {}).get(
                        descriptor.version
                    ),
                    descriptor,
                    source,
                )
            ]
            if not pending:
                return service.registry_path
            for descriptor in pending:
                _verify_source(source, descriptor)
            digest = _tree_digest(source)
            copied_root, created = _publish_copy(source, root / "shipped", digest)
            try:
                for descriptor in pending:
                    if created:
                        _verify_source(copied_root, descriptor)
                    input_root = (
                        copied_root / _module_relative_path(descriptor)
                    ).parent
                    # Fresh loaders avoid retaining temporary paths or cached graphs.
                    loader = DataLoader(input_dirs=[input_root])
                    loader.load_module_configs()
                    config = loader.get_initialized_config(descriptor.module_name)
                    if (config.name, config.version) != (
                        descriptor.module_name,
                        descriptor.version,
                    ):
                        raise ValueError(
                            "Hydrated module identity does not match its catalog"
                        )
                    loader.load_knowledge_base(descriptor.module_name)
                    versions = payload.modules.setdefault(descriptor.module_name, {})
                    old = versions.get(descriptor.version)
                    metadata = dict(old.model_extra or {}) if old is not None else {}
                    metadata.pop("path", None)
                    metadata.pop("data_root", None)
                    metadata.update(
                        {
                            "hydrated_from_sha256": descriptor.content_sha256,
                            "shipped_tree_sha256": digest,
                        }
                    )
                    if descriptor.medical_field is not None:
                        metadata.setdefault("medical_field", descriptor.medical_field)
                    entry = RegistryEntry.model_validate(
                        {
                            **metadata,
                            "sources": [
                                {"kind": "filesystem", "input_dirs": [str(input_root)]}
                            ],
                        }
                    )
                    versions[descriptor.version] = entry
                if initially_empty:
                    defaults = [
                        d
                        for d in catalog.knowledge_bases
                        if d.module_name == default_module and d.default
                    ]
                    if len(defaults) != 1:
                        raise ValueError(
                            f"No unique shipped default for {default_module!r}"
                        )
                    payload.active = RegistryActiveIdentity(
                        module_name=default_module,
                        version=defaults[0].version,
                    )
                service._write(payload)
            except Exception:
                if created:
                    shutil.rmtree(copied_root.parent, ignore_errors=True)
                raise
        clear_knowledge_base_resolver_caches()
        return service.registry_path
    except TerminologyError:
        raise
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        raise TerminologyError(
            409, f"Shipped terminology hydration failed: {exc}"
        ) from exc
