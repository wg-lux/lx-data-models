"""Shared legacy migration rule: infer a package kind from a package's own records.

The rule never guesses. It classifies only by the knowledge-base record models a
package defines itself (dependency records are ignored), never by folder names.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from lx_dtypes.models.contracts.package_kind import (
    PackageKind,
    package_kind_dependency_allowed,
)
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.models.model import FrozenContractModel
from lx_dtypes.utils.parser import camel_to_snake

# Any of these makes a package a report-template package.
REPORT_TEMPLATE_TRIGGER_MODELS = frozenset(
    {"report_template", "report_template_section"}
)
# Allowed alongside a trigger; on their own they are not classifiable.
REPORTING_REFERENCE_MODELS = frozenset({"report_finding"})
TERMINOLOGY_MODELS = frozenset(
    {
        "information_source_type",
        "information_source",
        "citation",
        "unit_type",
        "unit",
        "classification_choice_descriptor",
        "classification_choice",
        "classification_type",
        "classification",
        "intervention_type",
        "intervention",
        "finding_type",
        "finding",
        "indication_type",
        "indication",
        "examination_type",
        "examination",
        "classification_validator",
        "intervention_validator",
        "unit_validator",
        "findings_validator",
        "examination_validator",
        "time_reference",
        "electrical_curve_profile",
    }
)
APPLICATION_DATA_MODELS = frozenset({"reference_catalog", "center_employee_list"})
STUDY_MODELS = frozenset({"study_preset"})

LEGACY_KIND_MODEL_GROUPS: Mapping[str, frozenset[str]] = {
    "report_template_trigger": REPORT_TEMPLATE_TRIGGER_MODELS,
    "reporting_reference": REPORTING_REFERENCE_MODELS,
    "terminology": TERMINOLOGY_MODELS,
    "application_data": APPLICATION_DATA_MODELS,
    "study": STUDY_MODELS,
}


class PackageKindInference(FrozenContractModel):
    """Inferred kind (``None`` when not unambiguous) with a readable reason."""

    package_kind: PackageKind | None
    reason: str


def own_record_counts(kb: KnowledgeBase) -> dict[str, int]:
    """Count records defined by the package itself: its root module and the
    modules it composes through ``modules``; ``depends_on`` records are excluded."""
    owners = kb.composed_module_names()
    counts: Counter[str] = Counter()
    for model in KB_MODEL_NAMES_ORDERED:
        field = camel_to_snake(model)
        records = getattr(kb, field)
        counts[field] = sum(
            1 for record in records.values() if record.kb_module_name in owners
        )
    return {field: count for field, count in counts.items() if count}


def infer_legacy_package_kind(
    source: KnowledgeBase | Path,
    *,
    input_dirs: Sequence[Path] | None = None,
) -> PackageKindInference:
    """Apply the shared migration rule to one package's own records.

    ``source`` is a loaded knowledge base or the path of a root ``config.yaml``;
    a path is loaded through the strict ``load_package`` gate (``input_dirs``
    as there). Only the package's own records count: the root module and the
    modules it composes via ``modules``, never ``depends_on`` dependencies.
    """
    if isinstance(source, Path):
        from lx_dtypes.packages import load_package

        kb = load_package(source, input_dirs=input_dirs)
    else:
        if input_dirs is not None:
            raise TypeError("input_dirs applies only to a config.yaml path")
        kb = source
    counts = own_record_counts(kb)
    present = set(counts)
    summary = ", ".join(f"{name}={counts[name]}" for name in sorted(counts))
    if not present:
        return PackageKindInference(
            package_kind=None, reason="The package defines no records of its own."
        )
    if present & REPORT_TEMPLATE_TRIGGER_MODELS:
        return PackageKindInference(
            package_kind=PackageKind.report_templates,
            reason=f"Defines report templates or sections ({summary}).",
        )
    for kind, models in (
        (PackageKind.terminology, TERMINOLOGY_MODELS),
        (PackageKind.application_data, APPLICATION_DATA_MODELS),
        (PackageKind.study, STUDY_MODELS),
    ):
        if present <= models:
            return PackageKindInference(
                package_kind=kind,
                reason=f"Defines only {kind.value} records ({summary}).",
            )
    return PackageKindInference(
        package_kind=None,
        reason=f"Records do not determine one package kind ({summary}).",
    )


@dataclass(frozen=True)
class PackageKindDependencyFinding:
    """One dependency edge that breaks, or cannot be checked against, the kind rules."""

    module: str
    version: str
    package_kind: PackageKind | None
    dependency: str
    dependency_version: str
    dependency_kind: PackageKind | None
    status: Literal["violation", "unclassified"]

    def format(self) -> str:
        def label(kind: PackageKind | None) -> str:
            return "unclassified" if kind is None else kind.value

        return (
            f"{self.status}: {self.module}@{self.version} ({label(self.package_kind)})"
            f" -> {self.dependency}@{self.dependency_version}"
            f" ({label(self.dependency_kind)})"
        )


def loaded_package_kind_findings(
    kb: KnowledgeBase,
    *,
    package_kinds: Mapping[tuple[str, str], PackageKind] | None = None,
) -> tuple[PackageKindDependencyFinding, ...]:
    """Check the kind rules over the exact closure ``kb`` was loaded from.

    Each module is compared with every module of its resolved closure; the
    rule table is transitively closed, so this equals checking direct edges
    whenever kinds are known. Unrelated manifests are never read.
    """
    reviewed = package_kinds or {}
    configs = kb.resolved_module_configs()

    def kind_of(config: KnowledgeBaseConfig) -> PackageKind | None:
        listed = reviewed.get((config.name, config.version))
        if (
            listed is not None
            and config.package_kind is not None
            and listed != config.package_kind
        ):
            raise ValueError(
                f"{config.name}@{config.version} declares package_kind "
                f"{config.package_kind.value}, reviewed mapping lists {listed.value}"
            )
        return config.package_kind if config.package_kind is not None else listed

    findings: dict[tuple[str, str, str, str], PackageKindDependencyFinding] = {}
    for config in configs.values():
        kind = kind_of(config)
        for name in dict.fromkeys([*config.depends_on, *config.modules]):
            dependency = configs.get(name)
            if dependency is None:
                continue
            dependency_kind = kind_of(dependency)
            if kind is None or dependency_kind is None:
                status: Literal["violation", "unclassified"] = "unclassified"
            elif package_kind_dependency_allowed(kind, dependency_kind):
                continue
            else:
                status = "violation"
            key = (config.name, config.version, dependency.name, dependency.version)
            findings[key] = PackageKindDependencyFinding(
                module=config.name,
                version=config.version,
                package_kind=kind,
                dependency=dependency.name,
                dependency_version=dependency.version,
                dependency_kind=dependency_kind,
                status=status,
            )
    return tuple(findings[key] for key in sorted(findings))


def audit_package_kind_dependencies(
    config_path: Path,
    *,
    input_dirs: Sequence[Path] | None = None,
    package_kinds: Mapping[tuple[str, str], PackageKind] | None = None,
) -> tuple[PackageKindDependencyFinding, ...]:
    """Report dependency edges of one package closure against the kind rules.

    A module's kind is its declared ``config.yaml`` ``package_kind``, or the
    reviewed ``package_kinds`` entry for its exact ``(name, version)``; both
    must agree when both exist. Modules without either are unclassified and
    their edges are reported as such, never defaulted. This is an audit; it
    does not reject packages.
    """
    reviewed = package_kinds or {}
    root = KnowledgeBaseConfig.from_yaml_file(config_path.resolve())
    loader = DataLoader(
        input_dirs=list(input_dirs)
        if input_dirs is not None
        else [module_search_root(config_path.resolve())]
    )
    loader.load_module_configs()

    def kind_of(config: KnowledgeBaseConfig) -> PackageKind | None:
        listed = reviewed.get((config.name, config.version))
        if (
            listed is not None
            and config.package_kind is not None
            and listed != config.package_kind
        ):
            raise ValueError(
                f"{config.name}@{config.version} declares package_kind "
                f"{config.package_kind.value}, reviewed mapping lists {listed.value}"
            )
        return config.package_kind if config.package_kind is not None else listed

    findings: dict[tuple[str, str, str, str], PackageKindDependencyFinding] = {}
    visited: set[tuple[str, str]] = set()
    pending = [root]
    while pending:
        config = pending.pop()
        identity = (config.name, config.version)
        if identity in visited:
            continue
        visited.add(identity)
        kind = kind_of(config)
        edges = [(name, "dependency") for name in config.depends_on]
        edges.extend((name, "module") for name in config.modules)
        for name, relation in edges:
            dependency = loader.resolve_module_config(
                name,
                context_config=config,
                relation="module" if relation == "module" else "dependency",
            )
            pending.append(dependency)
            dependency_kind = kind_of(dependency)
            if kind is None or dependency_kind is None:
                status: Literal["violation", "unclassified"] = "unclassified"
            elif package_kind_dependency_allowed(kind, dependency_kind):
                continue
            else:
                status = "violation"
            key = (config.name, config.version, dependency.name, dependency.version)
            findings[key] = PackageKindDependencyFinding(
                module=config.name,
                version=config.version,
                package_kind=kind,
                dependency=dependency.name,
                dependency_version=dependency.version,
                dependency_kind=dependency_kind,
                status=status,
            )
    return tuple(findings[key] for key in sorted(findings))


__all__ = [
    "LEGACY_KIND_MODEL_GROUPS",
    "PackageKindDependencyFinding",
    "PackageKindInference",
    "audit_package_kind_dependencies",
    "infer_legacy_package_kind",
    "loaded_package_kind_findings",
    "own_record_counts",
]
