import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.models.contracts.reference_catalog import CatalogIdentity, ReferenceKind
from lx_dtypes.models.contracts.reference_migration import (
    ReferenceFieldDecision,
    ReferenceMigrationCatalog,
    ReferenceMigrationRule,
    ReferenceMigrationTarget,
    ReferenceRowMigration,
    ReferenceRowState,
    load_reference_migrations,
    plan_reference_migration,
)

SOURCE = ReferenceKind.INFORMATION_SOURCE


def _row(name: str, **fields: JsonValue) -> ReferenceRowState:
    return ReferenceRowState(
        kind=SOURCE, identity=CatalogIdentity(name=name), fields=fields
    )


def _target(*rules: ReferenceMigrationRule) -> ReferenceMigrationTarget:
    return ReferenceMigrationTarget(
        module="endoreg_reference", version="2.0.0", rules=list(rules)
    )


def test_legacy_unknown_description_fills_automatically() -> None:
    # endoreg_reference@1.1.0 wrote description=None; @2.0.0 ships text.
    existing = _row("unknown", name_de="Unbekannt", description=None)
    proposed = _row(
        "unknown", name_de="Unbekannt", description="Data source is unknown."
    )

    plan = plan_reference_migration([(existing, proposed)], _target())

    assert plan.automatic
    (row,) = plan.rows
    assert row.changes[0].decision == ReferenceFieldDecision.FILL_MISSING
    assert row.updates == {"description": "Data source is unknown."}
    assert ReferenceRowMigration.model_validate(row.model_dump(mode="json")) == row


@pytest.mark.parametrize("absent", [None, "", "unknown"])
def test_equivalent_absent_descriptions_are_unchanged(absent: str | None) -> None:
    plan = plan_reference_migration(
        [(_row("a", description=absent), _row("a", description=None))], _target()
    )
    assert plan.rows == []


def test_display_label_updates_automatically() -> None:
    plan = plan_reference_migration(
        [(_row("a", name_de="Alt"), _row("a", name_de="Neu"))], _target()
    )
    assert plan.rows[0].changes[0].decision == ReferenceFieldDecision.UPDATE_DISPLAY
    assert plan.automatic


def test_existing_text_is_never_overwritten_or_erased() -> None:
    plan = plan_reference_migration(
        [
            (_row("a", description="Old"), _row("a", description="New")),
            (_row("b", description="Kept"), _row("b", description=None)),
        ],
        _target(),
    )
    assert not plan.automatic
    assert [row.identity.name for row in plan.conflicts] == ["a", "b"]
    assert all(row.updates == {} for row in plan.conflicts)


def test_declared_rule_applies_only_to_its_exact_old_value() -> None:
    rule = ReferenceMigrationRule(
        kind=SOURCE,
        identity=CatalogIdentity(name="a"),
        field="url",
        existing="http://old",
        proposed="https://new",
        reason="Reviewed URL correction.",
    )
    matched = plan_reference_migration(
        [(_row("a", url="http://old"), _row("a", url="https://new"))], _target(rule)
    )
    assert matched.automatic
    assert matched.rows[0].changes[0].reason == "Reviewed URL correction."

    drifted = plan_reference_migration(
        [(_row("a", url="http://other"), _row("a", url="https://new"))], _target(rule)
    )
    assert not drifted.automatic


def test_rules_support_multiple_predecessors_and_distinguish_json_types() -> None:
    rules = [
        ReferenceMigrationRule(
            kind=SOURCE,
            identity=CatalogIdentity(name="a"),
            field="metadata",
            existing={"code": previous},
            proposed={"code": "final"},
            reason="Reviewed legacy representation.",
        )
        for previous in (1, "intermediate")
    ]
    target = _target(*rules)
    proposed = _row("a", metadata={"code": "final"})
    for rule in rules:
        plan = plan_reference_migration(
            [(_row("a", metadata=rule.existing), proposed)], target
        )
        assert plan.automatic
    drifted = plan_reference_migration(
        [(_row("a", metadata={"code": True}), proposed)], target
    )
    assert not drifted.automatic


def test_one_conflicting_field_blocks_the_whole_row() -> None:
    plan = plan_reference_migration(
        [
            (
                _row("a", name_de="Alt", url="x"),
                _row("a", name_de="Neu", url="y"),
            )
        ],
        _target(),
    )
    assert not plan.automatic
    assert plan.rows[0].updates == {}


def test_mismatched_exports_are_rejected() -> None:
    with pytest.raises(ValueError, match="different reference identities"):
        plan_reference_migration([(_row("a"), _row("b"))], _target())
    with pytest.raises(ValueError, match="different fields"):
        plan_reference_migration(
            [(_row("a", url=None), _row("a", description=None))], _target()
        )


def test_catalog_rejects_duplicates_and_noop_rules() -> None:
    rule = {
        "kind": "information_source",
        "identity": {"name": "a"},
        "field": "url",
        "existing": "x",
        "proposed": "y",
        "reason": "r",
    }
    target = {"module": "m", "version": "1", "rules": [rule, rule]}
    with pytest.raises(ValidationError, match="Duplicate migration rule"):
        ReferenceMigrationCatalog.model_validate(
            {"schema_version": 1, "targets": [target]}
        )
    with pytest.raises(ValidationError, match="must change"):
        ReferenceMigrationRule.model_validate({**rule, "proposed": "x"})


def test_packaged_catalog_loads_and_unknown_targets_have_no_rules() -> None:
    catalog = load_reference_migrations()
    assert catalog.target("endoreg_reference", "2.0.0").rules == []
