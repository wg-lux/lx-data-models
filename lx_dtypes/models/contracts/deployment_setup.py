"""Frozen v1 operator setup and portable dependency lock contracts."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PackageName = Annotated[
    str, Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
]
PackageVersion = Annotated[
    str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
]


class SetupModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class DeploymentSite(SetupModel):
    center_key: str = Field(
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
        description="Immutable host center key; selects the local application default.",
    )
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Center name. Existing rows with a different name are conflicts.",
    )

    @model_validator(mode="after")
    def normalized_name(self) -> Self:
        if self.name != self.name.strip():
            raise ValueError("site.name must not contain surrounding whitespace")
        return self


class DeploymentPackage(SetupModel):
    module: PackageName
    version: PackageVersion
    content_sha256: Sha256 | None = Field(
        default=None,
        description="Optional digest of the complete resolved source dependency closure.",
    )


class DeploymentStudyPackage(DeploymentPackage):
    activate: bool = Field(
        default=False,
        description="Select this registered terminology after database commit. False leaves active selection unchanged; no study records are created.",
    )


class DeploymentSetup(SetupModel):
    schema_version: Literal["1.0"]
    site: DeploymentSite
    reference_packages: list[DeploymentPackage] = Field(
        default_factory=list, max_length=100
    )
    study_packages: list[DeploymentStudyPackage] = Field(
        default_factory=list, max_length=100
    )
    adopt_existing: bool = Field(
        default=False,
        description="Explicitly adopt equivalent existing reference rows, preserving their primary keys. Never overwrite conflicts.",
    )

    @model_validator(mode="after")
    def unique_packages(self) -> Self:
        for packages in (self.reference_packages, self.study_packages):
            names = [p.module for p in packages]
            if len(names) != len(set(names)):
                raise ValueError("each package role may select a module only once")
        selected: dict[str, tuple[str, str | None]] = {}
        for package in [*self.reference_packages, *self.study_packages]:
            identity = (package.version, package.content_sha256)
            if package.module in selected and selected[package.module] != identity:
                raise ValueError(
                    "package roles must agree on module version and digest"
                )
            selected[package.module] = identity
        if sum(p.activate for p in self.study_packages) > 1:
            raise ValueError("at most one study package may activate")
        return self


class DeploymentSource(SetupModel):
    module: PackageName
    version: PackageVersion
    content_sha256: Sha256


class DeploymentPackageLock(DeploymentSource):
    sources: list[DeploymentSource] = Field(min_length=1)

    @model_validator(mode="after")
    def complete_digest(self) -> Self:
        names = [s.module for s in self.sources]
        if len(names) != len(set(names)):
            raise ValueError("resolved module sources must be unique")
        if not any(
            s.module == self.module and s.version == self.version for s in self.sources
        ):
            raise ValueError("resolved sources must contain the root identity")
        if self.content_sha256 != source_closure_digest(
            self.module, self.version, self.sources
        ):
            raise ValueError("source closure digest mismatch")
        return self


def source_closure_digest(
    module: str, version: str, sources: list[DeploymentSource]
) -> str:
    payload = {
        "module": module,
        "version": version,
        "sources": [s.model_dump() for s in sorted(sources, key=lambda s: s.module)],
    }
    return hashlib.sha256(
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


class DeploymentLock(SetupModel):
    schema_version: Literal["1.0"] = "1.0"
    setup: DeploymentSetup
    packages: list[DeploymentPackageLock]

    @model_validator(mode="after")
    def exact_selection(self) -> Self:
        expected = {
            (p.module, p.version)
            for p in [*self.setup.reference_packages, *self.setup.study_packages]
        }
        actual = [(p.module, p.version) for p in self.packages]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            raise ValueError(
                "lock packages must cover the manifest selections exactly once"
            )
        for selected in [*self.setup.reference_packages, *self.setup.study_packages]:
            locked = next(
                p
                for p in self.packages
                if (p.module, p.version) == (selected.module, selected.version)
            )
            if (
                selected.content_sha256 is not None
                and selected.content_sha256 != locked.content_sha256
            ):
                raise ValueError("selected package digest does not match the lock")
        return self
