"""Typed access to immutable knowledge bases shipped by ``lx-dtypes``."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
from importlib.resources.abc import Traversable
from pathlib import Path, PurePosixPath
from typing import Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BUILTIN_KNOWLEDGE_BASE_PROVIDER = "lx_dtypes.builtin"
RESOURCE_ANCHOR = "lx_dtypes"
CATALOG_RESOURCE = "data/catalog.json"


class _PackagedModuleIdentity(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class PackagedKnowledgeBase(BaseModel):
    """Identity and integrity metadata for one packaged knowledge base."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    medical_field: str | None = None
    resource_root: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    default: bool = False

    @field_validator("resource_root")
    @classmethod
    def validate_resource_root(cls, value: str) -> str:
        if "\\" in value:
            raise ValueError("resource_root must use POSIX separators")
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or ".." in path.parts:
            raise ValueError("resource_root must be a relative package path")
        return path.as_posix()

    def resource_directory(self) -> Traversable:
        resource: Traversable = files(RESOURCE_ANCHOR)
        for component in PurePosixPath(self.resource_root).parts:
            resource = resource.joinpath(component)
        if not resource.is_dir():
            raise FileNotFoundError(
                "Packaged knowledge-base directory is missing: "
                f"{self.module_name}@{self.version} ({self.resource_root})"
            )
        return resource

    def verified_resource_directory(self) -> Traversable:
        resource = self.resource_directory()
        config_resource = resource.joinpath("config.yaml")
        if not config_resource.is_file():
            raise PackagedKnowledgeBaseResourceError(
                f"Packaged knowledge base has no config.yaml: {self.module_name}"
            )
        config = _PackagedModuleIdentity.model_validate(
            yaml.safe_load(config_resource.read_text(encoding="utf-8"))
        )
        if (config.name, config.version) != (self.module_name, self.version):
            raise PackagedKnowledgeBaseResourceError(
                "Packaged knowledge-base catalog identity conflicts with config.yaml: "
                f"catalog {self.module_name}@{self.version}, config "
                f"{config.name}@{config.version}"
            )
        actual_digest = knowledge_base_content_sha256(resource)
        if actual_digest != self.content_sha256:
            raise PackagedKnowledgeBaseIntegrityError(
                "Packaged knowledge-base digest mismatch for "
                f"{self.module_name}@{self.version}: expected "
                f"{self.content_sha256}, got {actual_digest}"
            )
        return resource

    def installed_data_root(self) -> Path:
        """Return the current installation's data root for path-based loaders.

        The returned path is runtime state and must never be persisted. Wheels
        installed by Python package installers are unpacked into this directory.
        """

        module_resource = self.verified_resource_directory()
        if not isinstance(module_resource, Path):
            raise PackagedKnowledgeBaseResourceError(
                "The packaged knowledge base is not installed as a filesystem "
                "resource; consume resource_directory() instead."
            )
        return module_resource.parent


class PackagedKnowledgeBaseCatalog(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    knowledge_bases: tuple[PackagedKnowledgeBase, ...]

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        identities = [(item.module_name, item.version) for item in self.knowledge_bases]
        if len(identities) != len(set(identities)):
            raise ValueError("catalog contains duplicate module/version identities")
        modules = {item.module_name for item in self.knowledge_bases}
        default_counts = Counter(
            item.module_name for item in self.knowledge_bases if item.default
        )
        invalid_defaults = sorted(
            module_name for module_name in modules if default_counts[module_name] != 1
        )
        if invalid_defaults:
            raise ValueError(
                "each packaged module must have exactly one default version: "
                + ", ".join(invalid_defaults)
            )
        return self


class PackagedKnowledgeBaseResourceError(RuntimeError):
    """Raised when packaged resources cannot satisfy a loader contract."""


class PackagedKnowledgeBaseIntegrityError(PackagedKnowledgeBaseResourceError):
    """Raised when packaged bytes do not match their declared digest."""


_ROOT_RESOURCE_PATH = PurePosixPath()


def _iter_yaml_resources(
    root: Traversable,
    relative_to: PurePosixPath = _ROOT_RESOURCE_PATH,
) -> tuple[tuple[PurePosixPath, Traversable], ...]:
    resources: list[tuple[PurePosixPath, Traversable]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        relative_path = relative_to / child.name
        if child.is_dir():
            resources.extend(_iter_yaml_resources(child, relative_path))
        elif child.is_file() and relative_path.suffix.lower() in {".yaml", ".yml"}:
            resources.append((relative_path, child))
    return tuple(resources)


def knowledge_base_content_sha256(root: Traversable) -> str:
    """Hash YAML paths and bytes in deterministic POSIX-path order."""

    digest = sha256()
    for relative_path, resource in _iter_yaml_resources(root):
        digest.update(relative_path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(resource.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


@lru_cache(maxsize=1)
def get_packaged_knowledge_base_catalog() -> PackagedKnowledgeBaseCatalog:
    catalog_resource: Traversable = files(RESOURCE_ANCHOR)
    for component in PurePosixPath(CATALOG_RESOURCE).parts:
        catalog_resource = catalog_resource.joinpath(component)
    return PackagedKnowledgeBaseCatalog.model_validate_json(
        catalog_resource.read_text(encoding="utf-8")
    )


def list_packaged_knowledge_bases() -> tuple[PackagedKnowledgeBase, ...]:
    return get_packaged_knowledge_base_catalog().knowledge_bases


def get_packaged_knowledge_base(
    module_name: str,
    version: str | None = None,
) -> PackagedKnowledgeBase:
    candidates = [
        item
        for item in list_packaged_knowledge_bases()
        if item.module_name == module_name
        and (version is None or item.version == version)
        and (version is not None or item.default)
    ]
    if not candidates:
        requested = module_name if version is None else f"{module_name}@{version}"
        raise LookupError(f"Packaged knowledge base not found: {requested}")
    if len(candidates) != 1:
        raise RuntimeError(
            f"Ambiguous packaged knowledge base: {module_name}@{version or 'default'}"
        )
    return candidates[0]


__all__ = [
    "BUILTIN_KNOWLEDGE_BASE_PROVIDER",
    "PackagedKnowledgeBase",
    "PackagedKnowledgeBaseCatalog",
    "PackagedKnowledgeBaseIntegrityError",
    "PackagedKnowledgeBaseResourceError",
    "get_packaged_knowledge_base",
    "get_packaged_knowledge_base_catalog",
    "knowledge_base_content_sha256",
    "list_packaged_knowledge_bases",
]
