import json
from importlib.resources import files

import pytest
from pydantic import ValidationError

from lx_dtypes.knowledge_bases import list_packaged_knowledge_bases
from lx_dtypes.models.contracts.deployment_setup import (
    DeploymentKindError,
    DeploymentLock,
    DeploymentLockV1,
    DeploymentRole,
    DeploymentSetup,
    DeploymentSetupV1,
    PackageKindLookup,
    check_deployment_setup_kinds,
    migrate_deployment_setup_v1_to_v2,
)
from lx_dtypes.models.contracts.package_kind import PackageKind
from lx_dtypes.utils.deployment_setup import (
    parse_any_deployment_lock,
    parse_any_deployment_setup,
    parse_deployment_lock,
    parse_deployment_setup,
)

TEMPLATES = ["minimal", "coloreg", "training", "green_endoscopy"]
CATALOG_KINDS: PackageKindLookup = {
    (item.module_name, item.version): item.package_kind
    for item in list_packaged_knowledge_bases()
}
SITE = "site: {center_key: local, name: Local}\n"

# The shipped templates as released in schema v1, before their v2 migration.
V1_TEMPLATES = {
    "minimal": "reference_packages: []\nstudy_packages: []\n",
    "coloreg": (
        "reference_packages: [{module: endoreg_reference, version: 1.0.0}]\n"
        "study_packages: [{module: coloreg, version: 0.3.0, activate: false}]\n"
    ),
    "training": (
        "reference_packages: [{module: endoreg_reference, version: 1.0.0},"
        " {module: endoreg_workforce, version: 1.0.0}]\nstudy_packages: []\n"
    ),
    "green_endoscopy": (
        "reference_packages: [{module: endoreg_green_endoscopy, version: 1.0.0}]\n"
        "study_packages: []\n"
    ),
}
V1_SITES = {
    "training": "site: {center_key: training-center, name: Training Center}\n",
}


def _template(name: str) -> str:
    return files("lx_dtypes").joinpath("setup_templates", f"{name}.yml").read_text()


@pytest.mark.parametrize("name", TEMPLATES)
def test_shipped_templates_are_v2_and_kind_consistent(name: str) -> None:
    setup = parse_deployment_setup(_template(name))
    assert setup.schema_version == "2.0"
    assert not any(p.activate for p in setup.report_template_packages)
    assert not setup.adopt_existing
    check_deployment_setup_kinds(setup, CATALOG_KINDS)
    if name in {"coloreg", "training"}:
        assert (
            next(
                p.version
                for p in setup.reference_packages
                if p.module == "endoreg_reference"
            )
            == "2.0.0"
        )


def test_coloreg_template_selects_report_templates_role() -> None:
    setup = parse_deployment_setup(_template("coloreg"))
    assert [(p.module, p.version) for p in setup.report_template_packages] == [
        ("coloreg", "0.3.0")
    ]
    assert setup.study_packages == []


@pytest.mark.parametrize("name", TEMPLATES)
def test_shipped_v1_templates_migrate_roles_without_upgrading_package_pins(
    name: str,
) -> None:
    v1 = parse_any_deployment_setup(
        "schema_version: '1.0'\n"
        + V1_SITES.get(name, "site: {center_key: local-center, name: Local Center}\n")
        + V1_TEMPLATES[name]
        + "adopt_existing: false\n"
    )
    assert isinstance(v1, DeploymentSetupV1)
    migrated = migrate_deployment_setup_v1_to_v2(v1, CATALOG_KINDS)
    assert migrated.reference_packages == v1.reference_packages
    # Current templates select newer reference releases. Schema migration must
    # preserve the operator's original pins while producing the same v2 roles.
    expected = parse_deployment_setup(_template(name)).model_copy(
        update={"reference_packages": v1.reference_packages}
    )
    assert migrated == expected


def test_generated_editor_schema_matches_contract() -> None:
    schema = json.loads(
        files("lx_dtypes")
        .joinpath("setup_templates", "deployment_setup.schema.json")
        .read_text()
    )
    assert schema == DeploymentSetup.model_json_schema()


@pytest.mark.parametrize(
    "raw",
    [
        'schema_version: "2.0"\nschema_version: "2.0"',
        "site: &site {center_key: local, name: Local}\nother: *site",
        "!!python/object/apply:os.system [echo unsafe]",
        'schema_version: "2.0"\n' + SITE + "unknown: true",
        "schema_version: 2.0\n" + SITE,
        'schema_version: "2.0"\nsite: {center_key: local, name: "  "}',
        # v1 documents are not accepted where v2 is required.
        'schema_version: "1.0"\n' + SITE,
        # activate only on report_template_packages, at most once.
        'schema_version: "2.0"\n'
        + SITE
        + 'study_packages: [{module: a, version: "1", activate: true}]',
        'schema_version: "2.0"\n'
        + SITE
        + 'terminology_packages: [{module: a, version: "1", activate: false}]',
        'schema_version: "2.0"\n'
        + SITE
        + 'reference_packages: [{module: a, version: "1", activate: false}]',
        'schema_version: "2.0"\n'
        + SITE
        + "report_template_packages: ["
        + '{module: a, version: "1", activate: true},'
        + ' {module: b, version: "1", activate: true}]',
        # one module per role, matching pins across roles.
        'schema_version: "2.0"\n'
        + SITE
        + 'terminology_packages: [{module: a, version: "1"}, {module: a, version: "1"}]',
        'schema_version: "2.0"\n'
        + SITE
        + 'reference_packages: [{module: a, version: "1"}]\n'
        + 'terminology_packages: [{module: a, version: "2"}]',
        'schema_version: "2.0"\n'
        + SITE
        + 'reference_packages: [{module: a, version: "1", content_sha256: invalid}]',
    ],
)
def test_invalid_or_unsafe_setups_fail(raw: str) -> None:
    with pytest.raises(ValueError):
        parse_deployment_setup(raw)


def test_v1_remains_readable_with_its_invariants() -> None:
    v1 = parse_any_deployment_setup(
        'schema_version: "1.0"\n'
        + SITE
        + 'study_packages: [{module: a, version: "1", activate: true}]'
    )
    assert isinstance(v1, DeploymentSetupV1)
    with pytest.raises(ValueError):
        parse_any_deployment_setup(
            'schema_version: "1.0"\n'
            + SITE
            + "study_packages: ["
            + '{module: a, version: "1", activate: true},'
            + ' {module: b, version: "1", activate: true}]'
        )
    with pytest.raises(ValueError):
        parse_any_deployment_setup('schema_version: "3.0"\n' + SITE)


def _setup(**roles: list[dict[str, object]]) -> DeploymentSetup:
    return DeploymentSetup.model_validate(
        {
            "schema_version": "2.0",
            "site": {"center_key": "local", "name": "Local"},
            **roles,
        }
    )


def test_kind_check_reports_every_offending_package() -> None:
    setup = _setup(
        reference_packages=[{"module": "ref", "version": "1"}],
        terminology_packages=[{"module": "terms", "version": "1"}],
        report_template_packages=[{"module": "report", "version": "1"}],
        study_packages=[{"module": "study", "version": "1"}],
    )
    correct: dict[tuple[str, str], PackageKind | None] = {
        ("ref", "1"): PackageKind.application_data,
        ("terms", "1"): PackageKind.terminology,
        ("report", "1"): PackageKind.report_templates,
        ("study", "1"): PackageKind.study,
    }
    check_deployment_setup_kinds(setup, correct)
    wrong = {
        **correct,
        ("terms", "1"): PackageKind.report_templates,
        ("study", "1"): None,
    }
    with pytest.raises(DeploymentKindError) as error:
        check_deployment_setup_kinds(setup, wrong)
    problems = {(p.module, p.role, p.reason) for p in error.value.problems}
    assert problems == {
        ("terms", DeploymentRole.terminology_packages, "kind_mismatch"),
        ("study", DeploymentRole.study_packages, "unclassified"),
    }
    # A package missing from the lookup is unknown, never guessed.
    del correct[("ref", "1")]
    with pytest.raises(DeploymentKindError, match="ref@1"):
        check_deployment_setup_kinds(setup, correct)


def _v1(study: list[dict[str, object]]) -> DeploymentSetupV1:
    return DeploymentSetupV1.model_validate(
        {
            "schema_version": "1.0",
            "site": {"center_key": "local", "name": "Local"},
            "reference_packages": [{"module": "ref", "version": "1"}],
            "study_packages": study,
        }
    )


KINDS: PackageKindLookup = {
    ("ref", "1"): PackageKind.application_data,
    ("terms", "1"): PackageKind.terminology,
    ("report", "1"): PackageKind.report_templates,
    ("study", "1"): PackageKind.study,
    ("unknown", "1"): None,
}


def test_migration_moves_study_packages_to_their_kind_role() -> None:
    migrated = migrate_deployment_setup_v1_to_v2(
        _v1(
            [
                {"module": "terms", "version": "1"},
                {"module": "report", "version": "1", "activate": True},
                {"module": "study", "version": "1"},
            ]
        ),
        KINDS,
    )
    assert [p.module for p in migrated.reference_packages] == ["ref"]
    assert [p.module for p in migrated.terminology_packages] == ["terms"]
    assert [(p.module, p.activate) for p in migrated.report_template_packages] == [
        ("report", True)
    ]
    assert [p.module for p in migrated.study_packages] == ["study"]


@pytest.mark.parametrize(
    "study,reason",
    [
        ([{"module": "unknown", "version": "1"}], "unclassified"),
        ([{"module": "missing", "version": "1"}], "unclassified"),
        (
            [{"module": "terms", "version": "1", "activate": True}],
            "activate_not_report_template",
        ),
    ],
)
def test_migration_fails_closed(study: list[dict[str, object]], reason: str) -> None:
    with pytest.raises(DeploymentKindError) as error:
        migrate_deployment_setup_v1_to_v2(_v1(study), KINDS)
    assert [problem.reason for problem in error.value.problems] == [reason]


def test_migration_kind_checks_reference_packages() -> None:
    with pytest.raises(DeploymentKindError, match="reference_packages"):
        migrate_deployment_setup_v1_to_v2(
            _v1([]), {**KINDS, ("ref", "1"): PackageKind.terminology}
        )


def test_lock_rejects_missing_selected_package() -> None:
    with pytest.raises(ValidationError, match="cover the manifest"):
        parse_deployment_lock("""schema_version: "2.0"
setup:
  schema_version: "2.0"
  site: {center_key: local, name: Local}
  report_template_packages: [{module: a, version: "1"}]
packages: []
""")


def test_v1_lock_stays_readable_but_is_not_a_v2_lock() -> None:
    raw = """schema_version: "1.0"
setup:
  schema_version: "1.0"
  site: {center_key: local, name: Local}
packages: []
"""
    assert isinstance(parse_any_deployment_lock(raw), DeploymentLockV1)
    with pytest.raises(ValidationError):
        parse_deployment_lock(raw)
    assert DeploymentLock.model_fields["schema_version"].default == "2.0"
