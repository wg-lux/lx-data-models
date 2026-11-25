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
from pydantic import ConfigDict, Field, field_validator, model_validator

from lx_dtypes.models.contracts.package_kind import PackageKind
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.model import DtypesModel

BUILTIN_KNOWLEDGE_BASE_PROVIDER = "lx_dtypes.builtin"
RESOURCE_ANCHOR = "lx_dtypes"
CATALOG_RESOURCE = "data/catalog.json"
RELEASE_GUIDE = "docs/guides/terminology-releases.md"
CATALOG_TOOL = "uv run python scripts/kb_catalog.py"


def published_release_remediation(
    module_name: str,
    version: str,
    *,
    resource_root: str | None = None,
    default: bool = True,
) -> str:
    """Explain how to recover when a published release no longer matches its catalog.

    The text addresses both audiences that meet integrity errors: operators of an
    installed wheel and maintainers editing terminology in a repository checkout.
    """

    identity = f"{module_name}@{version}"
    checkout_path = f"lx_dtypes/{resource_root}" if resource_root else None
    restore = (
        f"`git restore {checkout_path}`" if checkout_path else "`git restore <path>`"
    )
    lines = [
        (
            f"{identity} is a published knowledge-base release, and published "
            "releases are immutable: hosts pin their exact bytes by module@version "
            "and digest."
        ),
        (
            "- Using an installed lx-dtypes: do not edit installed package files; "
            "reinstall the package (for example "
            "`uv sync --reinstall-package lx-dtypes`)."
        ),
    ]
    if default:
        lines.append(
            "- Maintaining terminology in an lx-dtypes checkout: to discard the edit, "
            f"run {restore}. To keep it, publish it as a new version with "
            f"`{CATALOG_TOOL} new-version {module_name} <next-version>`; that "
            "retains the committed bytes of "
            f"{identity} and carries your edits forward as the new default."
        )
    else:
        lines.append(
            f"- Maintaining terminology in an lx-dtypes checkout: {identity} is a "
            f"retained (non-default) release and is frozen. Run {restore}, then make "
            f"the correction in the current default release of {module_name} and "
            f"publish it with `{CATALOG_TOOL} new-version {module_name} <next-version>`."
        )
    lines.append(
        f"Run `{CATALOG_TOOL} status` for a full diagnosis; see {RELEASE_GUIDE}."
    )
    return "\n".join(lines)


def registered_digest_remediation(module_name: str, version: str) -> str:
    """Explain a host registry digest that differs from the installed release."""

    identity = f"{module_name}@{version}"
    return "\n".join(
        [
            (
                "The host registry recorded different content for this exact "
                "release than the installed lx-dtypes ships, so its terminology "
                "cannot be served safely."
            ),
            (
                "- Host operators: install the lx-dtypes version that originally "
                f"provided {identity}, or adopt a newer version of {module_name} "
                "through the host's terminology update process. Never edit the "
                "registry digest to make it match."
            ),
            (
                "- lx-dtypes maintainers: a published release was changed in place "
                "between package versions. Restore its original bytes and publish "
                f"the change as a new version with `{CATALOG_TOOL} new-version "
                f"{module_name} <next-version>`."
            ),
            f"See {RELEASE_GUIDE}.",
        ]
    )


class _PackagedModuleIdentity(DtypesModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    package_kind: PackageKind | None = None


class PackagedKnowledgeBase(DtypesModel):
    """Identity and integrity metadata for one packaged knowledge base."""

    model_config = ConfigDict(frozen=True)

    module_name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    medical_field: str | None = None
    resource_root: str = Field(min_length=1)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    default: bool = False
    # Optional only so retained catalogs of older hydrated copies stay readable;
    # the installed wheel catalog requires it (``require_package_kinds``).
    package_kind: PackageKind | None = None

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
                f"{self.module_name}@{self.version} ({self.resource_root}).\n"
                "The catalog lists this release but its files are not installed. "
                "Reinstall lx-dtypes; in a checkout, restore the directory with "
                f"`git restore lx_dtypes/{self.resource_root}` or correct "
                f"`resource_root` in lx_dtypes/{CATALOG_RESOURCE}. "
                f"Run `{CATALOG_TOOL} status` for a full diagnosis."
            )
        return resource

    def remediation(self) -> str:
        """Return maintainer and operator guidance for an integrity failure."""

        return published_release_remediation(
            self.module_name,
            self.version,
            resource_root=self.resource_root,
            default=self.default,
        )

    def verified_resource_directory(self) -> Traversable:
        resource = self.resource_directory()
        config_resource = resource.joinpath("config.yaml")
        if not config_resource.is_file():
            raise PackagedKnowledgeBaseResourceError(
                f"Packaged knowledge base has no config.yaml: {self.module_name}\n"
                + self.remediation()
            )
        config = _PackagedModuleIdentity.model_validate(
            yaml.safe_load(config_resource.read_text(encoding="utf-8"))
        )
        if (config.name, config.version) != (self.module_name, self.version):
            raise PackagedKnowledgeBaseResourceError(
                "Packaged knowledge-base catalog identity conflicts with config.yaml: "
                f"catalog {self.module_name}@{self.version}, config "
                f"{config.name}@{config.version}.\n"
                "Changing `name` or `version` in config.yaml does not create a new "
                "release; the catalog entry and the retained copy must change too.\n"
                + self.remediation()
            )
        if config.package_kind is not None and config.package_kind != self.package_kind:
            raise PackagedKnowledgeBaseResourceError(
                "Packaged knowledge-base catalog package_kind conflicts with "
                f"config.yaml for {self.module_name}@{self.version}: catalog "
                f"{self.package_kind}, config {config.package_kind}.\n"
                "A package kind is part of the reviewed release; see "
                "docs/guides/package-kinds.md.\n" + self.remediation()
            )
        actual_digest = knowledge_base_content_sha256(resource)
        if actual_digest != self.content_sha256:
            raise PackagedKnowledgeBaseIntegrityError(
                "Packaged knowledge-base digest mismatch for "
                f"{self.module_name}@{self.version}: expected "
                f"{self.content_sha256}, got {actual_digest}.\n"
                "The YAML files of this release (contents, names, or the set of "
                "files) differ from what the catalog recorded at release time.\n"
                + self.remediation()
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
        return module_search_root(module_resource / "config.yaml")


class PackagedKnowledgeBaseCatalog(DtypesModel):
    model_config = ConfigDict(frozen=True)

    schema_version: Literal[1]
    knowledge_bases: tuple[PackagedKnowledgeBase, ...]

    @model_validator(mode="after")
    def validate_catalog(self) -> Self:
        identities = [(item.module_name, item.version) for item in self.knowledge_bases]
        duplicates = sorted(
            f"{module_name}@{version}"
            for (module_name, version), count in Counter(identities).items()
            if count > 1
        )
        if duplicates:
            raise ValueError(
                "catalog contains duplicate module/version identities: "
                + ", ".join(duplicates)
                + ". Each published release needs a distinct version; use "
                f"`{CATALOG_TOOL} new-version <module> <next-version>`."
            )
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
                + ". Set `default: true` on the newest release and `false` on "
                "retained ones in lx_dtypes/data/catalog.json."
            )
        return self

    def require_package_kinds(self) -> Self:
        """Fail unless every entry carries a reviewed ``package_kind``."""

        missing = sorted(
            f"{item.module_name}@{item.version}"
            for item in self.knowledge_bases
            if item.package_kind is None
        )
        if missing:
            raise PackagedKnowledgeBaseResourceError(
                "Packaged knowledge-base catalog entries lack package_kind: "
                + ", ".join(missing)
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
    ).require_package_kinds()


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
    "published_release_remediation",
    "registered_digest_remediation",
]
