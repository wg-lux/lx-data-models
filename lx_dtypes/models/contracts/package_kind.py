"""Package kinds and the dependency rules between them.

A package kind classifies one versioned knowledge-base package. It is declared
explicitly; an absent kind means *unclassified* and is never defaulted.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class PackageKind(StrEnum):
    """The exact set of package kinds of the shared package contract v1."""

    terminology = "terminology"
    report_templates = "report_templates"
    study = "study"
    application_data = "application_data"


PACKAGE_KIND_ALLOWED_DEPENDENCIES: Mapping[PackageKind, frozenset[PackageKind]] = (
    MappingProxyType(
        {
            PackageKind.terminology: frozenset(
                {PackageKind.terminology, PackageKind.application_data}
            ),
            PackageKind.report_templates: frozenset(
                {
                    PackageKind.terminology,
                    PackageKind.report_templates,
                    PackageKind.application_data,
                }
            ),
            PackageKind.study: frozenset(
                {
                    PackageKind.terminology,
                    PackageKind.report_templates,
                    PackageKind.application_data,
                }
            ),
            PackageKind.application_data: frozenset(
                {PackageKind.application_data, PackageKind.terminology}
            ),
        }
    )
)


def package_kind_dependency_allowed(
    kind: PackageKind, dependency_kind: PackageKind
) -> bool:
    """Return whether a ``kind`` package may depend on a ``dependency_kind`` package.

    The table is transitively closed: checking every module of a resolved
    dependency closure gives the same verdict as checking direct edges.
    """

    return dependency_kind in PACKAGE_KIND_ALLOWED_DEPENDENCIES[kind]


__all__ = [
    "PACKAGE_KIND_ALLOWED_DEPENDENCIES",
    "PackageKind",
    "package_kind_dependency_allowed",
]
