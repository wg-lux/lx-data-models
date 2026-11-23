"""Portable package manifests (``lx-package/1``) and channel indexes (``lx-package-channel/1``).

Both documents are transport metadata only. They never carry patient data and
never replace validation of the package contents by the package import gate.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Literal, Self

from pydantic import AwareDatetime, Field, field_validator, model_validator

from lx_dtypes.models.contracts.package_kind import PackageKind
from lx_dtypes.models.model import FrozenContractModel

LX_PACKAGE_MANIFEST_FILENAME = "lx-package.json"
LX_PACKAGE_MANIFEST_SCHEMA = "lx-package/1"
PACKAGE_CHANNEL_INDEX_FILENAME = "channel.json"
PACKAGE_CHANNEL_INDEX_SCHEMA = "lx-package-channel/1"

_SHA256_PATTERN = r"^[0-9a-f]{64}$"


def _path_safe_identity(value: str, label: str) -> str:
    if (
        not value
        or value != value.strip()
        or value in {".", ".."}
        or any(character in value for character in "/\\\0@")
    ):
        raise ValueError(
            f"package {label} must be a non-empty, path-safe value without '@'"
        )
    return value


def _require_utc(value: AwareDatetime, label: str) -> AwareDatetime:
    if value.utcoffset() != timedelta(0):
        raise ValueError(f"{label} must be a UTC timestamp")
    return value


class LxPackageManifest(FrozenContractModel):
    """Root ``lx-package.json`` of an exported or shared package ZIP.

    It must agree with the archive's root ``config.yaml``; consumers compare
    ``name``, ``version`` and ``package_kind`` before importing the package.
    """

    schema_: Literal["lx-package/1"] = Field(alias="schema")
    name: str
    version: str
    package_kind: PackageKind = Field(strict=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _path_safe_identity(value, "name")

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        return _path_safe_identity(value, "version")

    def to_json_bytes(self) -> bytes:
        """Return the deterministic UTF-8 file content written into package ZIPs."""

        payload = self.model_dump(mode="json", by_alias=True)
        return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


class PackageChannelEntry(FrozenContractModel):
    """One immutable, content-addressed package release listed by a channel."""

    name: str
    version: str
    package_kind: PackageKind = Field(strict=False)
    sha256: str = Field(pattern=_SHA256_PATTERN)
    size: int = Field(gt=0)
    path: str
    published_at: AwareDatetime = Field(strict=False)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _path_safe_identity(value, "name")

    @field_validator("version")
    @classmethod
    def validate_version(cls, value: str) -> str:
        return _path_safe_identity(value, "version")

    @field_validator("published_at")
    @classmethod
    def validate_published_at(cls, value: AwareDatetime) -> AwareDatetime:
        return _require_utc(value, "published_at")

    @model_validator(mode="after")
    def validate_content_address(self) -> Self:
        if self.path != f"packages/{self.sha256}.zip":
            raise ValueError("path must equal packages/<sha256>.zip")
        return self

    def matches_manifest(self, manifest: LxPackageManifest) -> bool:
        """Return whether a package's own manifest declares this entry's identity."""

        return (self.name, self.version, self.package_kind) == (
            manifest.name,
            manifest.version,
            manifest.package_kind,
        )


class PackageChannelIndex(FrozenContractModel):
    """The ``channel.json`` document at the root of a read-only package channel."""

    schema_: Literal["lx-package-channel/1"] = Field(alias="schema")
    channel: str = Field(min_length=1)
    generated_at: AwareDatetime = Field(strict=False)
    packages: tuple[PackageChannelEntry, ...]

    @field_validator("channel")
    @classmethod
    def validate_channel(cls, value: str) -> str:
        return _path_safe_identity(value, "channel")

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: AwareDatetime) -> AwareDatetime:
        return _require_utc(value, "generated_at")

    @model_validator(mode="after")
    def validate_immutable_identities(self) -> Self:
        identities = [(entry.name, entry.version) for entry in self.packages]
        if len(identities) != len(set(identities)):
            raise ValueError("channel lists a package name/version more than once")
        digests = [entry.sha256 for entry in self.packages]
        if len(digests) != len(set(digests)):
            raise ValueError("channel lists the same package bytes more than once")
        return self

    def entry(self, name: str, version: str) -> PackageChannelEntry:
        """Return the exact ``name@version`` entry or raise ``LookupError``."""

        for candidate in self.packages:
            if (candidate.name, candidate.version) == (name, version):
                return candidate
        raise LookupError(f"Channel does not list package {name}@{version}")


__all__ = [
    "LX_PACKAGE_MANIFEST_FILENAME",
    "LX_PACKAGE_MANIFEST_SCHEMA",
    "PACKAGE_CHANNEL_INDEX_FILENAME",
    "PACKAGE_CHANNEL_INDEX_SCHEMA",
    "LxPackageManifest",
    "PackageChannelEntry",
    "PackageChannelIndex",
]
