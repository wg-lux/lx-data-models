"""Automatic, auditable migration of persisted reference rows to a newer package.

A host exports each existing reference row and the row proposed by the target
package into :class:`ReferenceRowState`. :func:`plan_reference_migration`
classifies every differing field without touching storage:

- ``update_display``: a display-only label (``name_de``) changed.
- ``fill_missing``: absent free text (``description``) gains authored text.
- ``declared``: a reviewed rule in ``reference_migrations.yml`` names this exact
  old and new value for the target package.
- ``conflict``: anything else, including erasing existing text.

Every non-conflicting change is safe to apply automatically. Conflicts are all
reported together so one dry run shows the complete review scope. The host owns
persistence, transactions and receipts; this module never writes.
"""

from __future__ import annotations

import json
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.factories.literals import normalize_missing_text
from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.models.contracts.reference_catalog import CatalogIdentity, ReferenceKind
from lx_dtypes.models.model import FrozenContractModel
from lx_dtypes.utils.study_setup_yaml import parse_setup_yaml

# Display-only labels: never identity, never clinical meaning.
DISPLAY_FIELDS: frozenset[str] = frozenset({"name_de"})
# Free text that may be filled when absent. Never overwritten, never erased.
FILLABLE_TEXT_FIELDS: frozenset[str] = frozenset({"description"})

REFERENCE_MIGRATIONS_FILE = "reference_migrations.yml"


def _value_key(value: JsonValue) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _same_value(left: JsonValue, right: JsonValue) -> bool:
    if type(left) is not type(right) or left != right:
        return False
    if isinstance(left, (dict, list)):
        return _value_key(left) == _value_key(right)
    return True


class ReferenceFieldDecision(StrEnum):
    UPDATE_DISPLAY = "update_display"
    FILL_MISSING = "fill_missing"
    DECLARED = "declared"
    CONFLICT = "conflict"


class ReferenceRowState(FrozenContractModel):
    """One reference row as persisted, or as proposed by a package."""

    kind: ReferenceKind = Field(strict=False)
    identity: CatalogIdentity
    fields: dict[str, JsonValue]


class ReferenceMigrationRule(FrozenContractModel):
    """A reviewed field change that may not be classified as safe automatically."""

    kind: ReferenceKind = Field(strict=False)
    identity: CatalogIdentity
    field: str = Field(min_length=1)
    existing: JsonValue
    proposed: JsonValue
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def changes_something(self) -> Self:
        if _same_value(self.existing, self.proposed):
            raise ValueError("A migration rule must change the field value")
        return self


class ReferenceMigrationTarget(FrozenContractModel):
    """Reviewed rules for migrating existing rows into one exact package version."""

    module: str = Field(min_length=1)
    version: str = Field(min_length=1)
    rules: list[ReferenceMigrationRule]

    @model_validator(mode="after")
    def unique_rules(self) -> Self:
        keys = [
            (
                rule.kind,
                rule.identity.name,
                rule.identity.version,
                rule.field,
                _value_key(rule.existing),
            )
            for rule in self.rules
        ]
        if len(keys) != len(set(keys)):
            raise ValueError(
                f"Duplicate migration rule for {self.module}@{self.version}"
            )
        return self

    def rule_for(
        self,
        kind: ReferenceKind,
        identity: CatalogIdentity,
        field: str,
        *,
        existing: JsonValue,
    ) -> ReferenceMigrationRule | None:
        return next(
            (
                rule
                for rule in self.rules
                if rule.kind == kind
                and rule.identity == identity
                and rule.field == field
                and _same_value(rule.existing, existing)
            ),
            None,
        )


class ReferenceMigrationCatalog(FrozenContractModel):
    """The packaged ``reference_migrations.yml`` sidecar."""

    schema_version: Literal[1]
    targets: list[ReferenceMigrationTarget]

    @model_validator(mode="after")
    def unique_targets(self) -> Self:
        keys = [(target.module, target.version) for target in self.targets]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate reference migration target")
        return self

    def target(self, module: str, version: str) -> ReferenceMigrationTarget:
        """Return reviewed rules for a target; no declared rules is an empty set."""
        for target in self.targets:
            if target.module == module and target.version == version:
                return target
        return ReferenceMigrationTarget(module=module, version=version, rules=[])


class ReferenceFieldMigration(FrozenContractModel):
    field: str
    existing: JsonValue
    proposed: JsonValue
    decision: ReferenceFieldDecision = Field(strict=False)
    reason: str | None = None


class ReferenceRowMigration(FrozenContractModel):
    kind: ReferenceKind = Field(strict=False)
    identity: CatalogIdentity
    changes: list[ReferenceFieldMigration]

    @model_validator(mode="after")
    def unique_changes(self) -> Self:
        if len({change.field for change in self.changes}) != len(self.changes):
            raise ValueError("Duplicate field in reference migration")
        return self

    @property
    def automatic(self) -> bool:
        return all(
            change.decision != ReferenceFieldDecision.CONFLICT
            for change in self.changes
        )

    @property
    def updates(self) -> dict[str, JsonValue]:
        """Field values to write; empty unless the whole row migrates automatically."""
        if not self.automatic:
            return {}
        return {change.field: change.proposed for change in self.changes}


class ReferenceMigrationPlan(FrozenContractModel):
    module: str
    version: str
    rows: list[ReferenceRowMigration]

    @property
    def automatic(self) -> bool:
        return all(row.automatic for row in self.rows)

    @property
    def conflicts(self) -> list[ReferenceRowMigration]:
        return [row for row in self.rows if not row.automatic]


def _is_missing_text(value: JsonValue) -> bool:
    return value is None or (
        isinstance(value, str) and not normalize_missing_text(value)
    )


def _classify(
    field: str,
    existing: JsonValue,
    proposed: JsonValue,
    rule: ReferenceMigrationRule | None,
) -> ReferenceFieldMigration | None:
    if _same_value(existing, proposed):
        return None
    if field in FILLABLE_TEXT_FIELDS and _is_missing_text(existing):
        if _is_missing_text(proposed):
            return None  # Equivalent absence, not a change.
        if isinstance(proposed, str):
            return ReferenceFieldMigration(
                field=field,
                existing=existing,
                proposed=proposed,
                decision=ReferenceFieldDecision.FILL_MISSING,
            )
    if rule is not None and _same_value(rule.proposed, proposed):
        return ReferenceFieldMigration(
            field=field,
            existing=existing,
            proposed=proposed,
            decision=ReferenceFieldDecision.DECLARED,
            reason=rule.reason,
        )
    if field in DISPLAY_FIELDS:
        return ReferenceFieldMigration(
            field=field,
            existing=existing,
            proposed=proposed,
            decision=ReferenceFieldDecision.UPDATE_DISPLAY,
        )
    return ReferenceFieldMigration(
        field=field,
        existing=existing,
        proposed=proposed,
        decision=ReferenceFieldDecision.CONFLICT,
    )


def plan_reference_row_migration(
    existing: ReferenceRowState,
    proposed: ReferenceRowState,
    target: ReferenceMigrationTarget,
) -> ReferenceRowMigration:
    """Classify every differing field of one row.

    Raises:
        ValueError: If the rows are not the same identity or expose different
            field sets; that is a host export defect, not a data conflict.
    """
    if (existing.kind, existing.identity) != (proposed.kind, proposed.identity):
        raise ValueError("Cannot migrate between different reference identities")
    if set(existing.fields) != set(proposed.fields):
        missing = sorted(set(existing.fields) ^ set(proposed.fields))
        raise ValueError(
            f"{proposed.kind}.{proposed.identity.name} exports different fields: {missing}"
        )
    changes = [
        change
        for field in sorted(proposed.fields)
        if (
            change := _classify(
                field,
                existing.fields[field],
                proposed.fields[field],
                target.rule_for(
                    proposed.kind,
                    proposed.identity,
                    field,
                    existing=existing.fields[field],
                ),
            )
        )
        is not None
    ]
    return ReferenceRowMigration(
        kind=proposed.kind, identity=proposed.identity, changes=changes
    )


def plan_reference_migration(
    pairs: list[tuple[ReferenceRowState, ReferenceRowState]],
    target: ReferenceMigrationTarget,
) -> ReferenceMigrationPlan:
    """Plan all ``(existing, proposed)`` row pairs; unchanged rows are omitted."""
    rows = [
        row
        for existing, proposed in pairs
        if (row := plan_reference_row_migration(existing, proposed, target)).changes
    ]
    return ReferenceMigrationPlan(
        module=target.module, version=target.version, rows=rows
    )


def load_reference_migrations(path: Path | None = None) -> ReferenceMigrationCatalog:
    """Load the reviewed migration rules shipped with the package."""
    source = (
        path
        if path is not None
        else files("lx_dtypes").joinpath("data", REFERENCE_MIGRATIONS_FILE)
    )
    return ReferenceMigrationCatalog.model_validate(
        parse_setup_yaml(source.read_text(encoding="utf-8"))
    )


__all__ = [
    "DISPLAY_FIELDS",
    "FILLABLE_TEXT_FIELDS",
    "REFERENCE_MIGRATIONS_FILE",
    "ReferenceFieldDecision",
    "ReferenceFieldMigration",
    "ReferenceMigrationCatalog",
    "ReferenceMigrationPlan",
    "ReferenceMigrationRule",
    "ReferenceMigrationTarget",
    "ReferenceRowMigration",
    "ReferenceRowState",
    "load_reference_migrations",
    "plan_reference_migration",
    "plan_reference_row_migration",
]
