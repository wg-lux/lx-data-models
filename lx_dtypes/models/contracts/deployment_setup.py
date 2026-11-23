"""Operator deployment setup (v2, v1 readable for migration) and lock contracts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.models.contracts.package_kind import PackageKind
from lx_dtypes.models.model import FrozenContractModel

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
PackageName = Annotated[
    str, Field(min_length=1, max_length=255, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
]
PackageVersion = Annotated[
    str, Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")
]


class SetupModel(FrozenContractModel):
    pass


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
    """v1 study selection; ``activate`` selected the registered knowledge base."""

    activate: bool = Field(
        default=False,
        description="Select this registered terminology after database commit. False leaves active selection unchanged; no study records are created.",
    )


class DeploymentReportTemplatePackage(DeploymentPackage):
    activate: bool = Field(
        default=False,
        description="Select this registered report-template package after database commit. False leaves the active selection unchanged. At most one selection may activate.",
    )


class DeploymentRole(StrEnum):
    """v2 package roles; each requires exactly one package kind."""

    reference_packages = "reference_packages"
    terminology_packages = "terminology_packages"
    report_template_packages = "report_template_packages"
    study_packages = "study_packages"


DEPLOYMENT_ROLE_KINDS: Mapping[DeploymentRole, PackageKind] = MappingProxyType(
    {
        DeploymentRole.reference_packages: PackageKind.application_data,
        DeploymentRole.terminology_packages: PackageKind.terminology,
        DeploymentRole.report_template_packages: PackageKind.report_templates,
        DeploymentRole.study_packages: PackageKind.study,
    }
)
ROLE_FOR_KIND: Mapping[PackageKind, DeploymentRole] = MappingProxyType(
    {kind: role for role, kind in DEPLOYMENT_ROLE_KINDS.items()}
)


def _check_role_selections(roles: Sequence[Sequence[DeploymentPackage]]) -> None:
    """Shared v1/v2 invariants: one module per role, matching pins across roles."""
    for packages in roles:
        names = [p.module for p in packages]
        if len(names) != len(set(names)):
            raise ValueError("each package role may select a module only once")
    selected: dict[str, tuple[str, str | None]] = {}
    for packages in roles:
        for package in packages:
            identity = (package.version, package.content_sha256)
            if package.module in selected and selected[package.module] != identity:
                raise ValueError(
                    "package roles must agree on module version and digest"
                )
            selected[package.module] = identity


class DeploymentSetupV1(SetupModel):
    """Frozen v1 document. Readable only to migrate it to v2."""

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
        _check_role_selections((self.reference_packages, self.study_packages))
        if sum(p.activate for p in self.study_packages) > 1:
            raise ValueError("at most one study package may activate")
        return self

    def selected_packages(self) -> list[DeploymentPackage]:
        return [*self.reference_packages, *self.study_packages]


class DeploymentSetup(SetupModel):
    """v2 deployment document with explicit, kind-checked package roles."""

    schema_version: Literal["2.0"]
    site: DeploymentSite
    reference_packages: list[DeploymentPackage] = Field(
        default_factory=list,
        max_length=100,
        description="application_data packages; the host projects their reference catalogue closure.",
    )
    terminology_packages: list[DeploymentPackage] = Field(
        default_factory=list,
        max_length=100,
        description="terminology packages registered for the site.",
    )
    report_template_packages: list[DeploymentReportTemplatePackage] = Field(
        default_factory=list,
        max_length=100,
        description="report_templates packages; at most one may activate.",
    )
    study_packages: list[DeploymentPackage] = Field(
        default_factory=list,
        max_length=100,
        description="study packages; never activated by the setup document.",
    )
    adopt_existing: bool = Field(
        default=False,
        description="Explicitly adopt equivalent existing reference rows, preserving their primary keys. Never overwrite conflicts.",
    )

    @model_validator(mode="after")
    def unique_packages(self) -> Self:
        _check_role_selections([packages for _, packages in self.roles()])
        if sum(p.activate for p in self.report_template_packages) > 1:
            raise ValueError("at most one report_template_packages entry may activate")
        return self

    def roles(self) -> tuple[tuple[DeploymentRole, Sequence[DeploymentPackage]], ...]:
        return (
            (DeploymentRole.reference_packages, self.reference_packages),
            (DeploymentRole.terminology_packages, self.terminology_packages),
            (DeploymentRole.report_template_packages, self.report_template_packages),
            (DeploymentRole.study_packages, self.study_packages),
        )

    def selected_packages(self) -> list[DeploymentPackage]:
        return [package for _, packages in self.roles() for package in packages]


AnyDeploymentSetup = Annotated[
    DeploymentSetupV1 | DeploymentSetup, Field(discriminator="schema_version")
]
PackageKindLookup = Mapping[tuple[str, str], PackageKind | None]


class DeploymentKindProblem(FrozenContractModel):
    """One selection whose package kind does not fit its role."""

    role: DeploymentRole | None
    module: str
    version: str
    expected_kind: PackageKind | None
    actual_kind: PackageKind | None
    reason: Literal["unclassified", "kind_mismatch", "activate_not_report_template"]

    def format(self) -> str:
        actual = self.actual_kind.value if self.actual_kind else "unclassified"
        if self.reason == "unclassified":
            return (
                f"{self.module}@{self.version}: package kind is unknown or unclassified"
            )
        if self.reason == "activate_not_report_template":
            return (
                f"{self.module}@{self.version}: activate is only allowed for "
                f"report_templates packages, not {actual}"
            )
        role = self.role.value if self.role else "?"
        expected = self.expected_kind.value if self.expected_kind else "?"
        return f"{self.module}@{self.version} in {role}: expected {expected}, found {actual}"


class DeploymentKindError(ValueError):
    """Every selection that is unclassified or in the wrong role, never guessed."""

    def __init__(self, problems: Sequence[DeploymentKindProblem]) -> None:
        self.problems = tuple(problems)
        super().__init__(
            "Deployment package kinds do not match their roles: "
            + "; ".join(problem.format() for problem in self.problems)
        )


def check_deployment_setup_kinds(
    setup: DeploymentSetup, kind_lookup: PackageKindLookup
) -> None:
    """Require each selection's kind (declared, catalog or migrated) to fit its role."""
    problems: list[DeploymentKindProblem] = []
    for role, packages in setup.roles():
        expected = DEPLOYMENT_ROLE_KINDS[role]
        for package in packages:
            actual = kind_lookup.get((package.module, package.version))
            if actual is None or actual != expected:
                problems.append(
                    DeploymentKindProblem(
                        role=role,
                        module=package.module,
                        version=package.version,
                        expected_kind=expected,
                        actual_kind=actual,
                        reason="unclassified" if actual is None else "kind_mismatch",
                    )
                )
    if problems:
        raise DeploymentKindError(problems)


def migrate_deployment_setup_v1_to_v2(
    setup: DeploymentSetupV1, kind_lookup: PackageKindLookup
) -> DeploymentSetup:
    """Map v1 roles to v2 by package kind; fail on any unclassified selection.

    v1 ``reference_packages`` stay reference packages. Each v1 study selection
    moves to the role of its kind; ``activate: true`` survives only on a
    ``report_templates`` package. The result is kind-checked as v2.
    """
    roles: dict[DeploymentRole, list[dict[str, object]]] = {
        role: [] for role in DeploymentRole
    }
    problems: list[DeploymentKindProblem] = []
    for package in setup.reference_packages:
        roles[DeploymentRole.reference_packages].append(package.model_dump())
    for package in setup.study_packages:
        kind = kind_lookup.get((package.module, package.version))
        if kind is None:
            problems.append(
                DeploymentKindProblem(
                    role=None,
                    module=package.module,
                    version=package.version,
                    expected_kind=None,
                    actual_kind=None,
                    reason="unclassified",
                )
            )
            continue
        role = ROLE_FOR_KIND[kind]
        selection = package.model_dump(exclude={"activate"})
        if role is DeploymentRole.report_template_packages:
            selection["activate"] = package.activate
        elif package.activate:
            problems.append(
                DeploymentKindProblem(
                    role=role,
                    module=package.module,
                    version=package.version,
                    expected_kind=PackageKind.report_templates,
                    actual_kind=kind,
                    reason="activate_not_report_template",
                )
            )
            continue
        roles[role].append(selection)
    if problems:
        raise DeploymentKindError(problems)
    migrated = DeploymentSetup.model_validate(
        {
            "schema_version": "2.0",
            "site": setup.site.model_dump(),
            **{role.value: selections for role, selections in roles.items()},
            "adopt_existing": setup.adopt_existing,
        }
    )
    check_deployment_setup_kinds(migrated, kind_lookup)
    return migrated


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


def _check_lock(
    selected: Sequence[DeploymentPackage], packages: Sequence[DeploymentPackageLock]
) -> None:
    expected = {(p.module, p.version) for p in selected}
    actual = [(p.module, p.version) for p in packages]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise ValueError(
            "lock packages must cover the manifest selections exactly once"
        )
    for chosen in selected:
        locked = next(
            p
            for p in packages
            if (p.module, p.version) == (chosen.module, chosen.version)
        )
        if (
            chosen.content_sha256 is not None
            and chosen.content_sha256 != locked.content_sha256
        ):
            raise ValueError("selected package digest does not match the lock")


class DeploymentLockV1(SetupModel):
    """Frozen v1 lock; readable for existing receipts only."""

    schema_version: Literal["1.0"] = "1.0"
    setup: DeploymentSetupV1
    packages: list[DeploymentPackageLock]

    @model_validator(mode="after")
    def exact_selection(self) -> Self:
        _check_lock(self.setup.selected_packages(), self.packages)
        return self


class DeploymentLock(SetupModel):
    schema_version: Literal["2.0"] = "2.0"
    setup: DeploymentSetup
    packages: list[DeploymentPackageLock]

    @model_validator(mode="after")
    def exact_selection(self) -> Self:
        _check_lock(self.setup.selected_packages(), self.packages)
        return self


__all__ = [
    "DEPLOYMENT_ROLE_KINDS",
    "AnyDeploymentSetup",
    "DeploymentKindError",
    "DeploymentKindProblem",
    "DeploymentLock",
    "DeploymentLockV1",
    "DeploymentPackage",
    "DeploymentPackageLock",
    "DeploymentReportTemplatePackage",
    "DeploymentRole",
    "DeploymentSetup",
    "DeploymentSetupV1",
    "DeploymentSite",
    "DeploymentSource",
    "DeploymentStudyPackage",
    "PackageKindLookup",
    "check_deployment_setup_kinds",
    "migrate_deployment_setup_v1_to_v2",
    "source_closure_digest",
]
