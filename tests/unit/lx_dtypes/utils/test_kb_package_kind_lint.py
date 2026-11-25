"""Package-kind, manifest, validator and German-name diagnostics of the package lint."""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
import yaml

from lx_dtypes.knowledge_bases import (
    PackagedKnowledgeBaseCatalog,
    get_packaged_knowledge_base,
    get_packaged_knowledge_base_catalog,
)
from lx_dtypes.models.contracts import PackageKind
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
)
from lx_dtypes.scripts import lint_kb_yaml as cli
from lx_dtypes.utils.kb_package_lint import (
    check_kb_package,
    check_packaged_knowledge_bases,
)

TERMS = [
    {"model": "finding", "name": "lesion", "description": "Synthetic finding."},
    {"model": "examination", "name": "exam", "findings": ["lesion"]},
]


@pytest.fixture(autouse=True)
def isolated_caches():
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


def module(
    root: Path,
    name: str,
    records: Sequence[Mapping[str, object]],
    *,
    kind: str | None = None,
    depends_on: tuple[str, ...] = (),
    german: bool = True,
) -> Path:
    directory = root / name
    directory.mkdir(parents=True)
    config: dict[str, object] = {
        "name": name,
        "version": "1.0.0",
        "depends_on": list(depends_on),
        "data": {"files": ["records.yml"]},
    }
    if kind is not None:
        config["package_kind"] = kind
    (directory / "config.yaml").write_text(yaml.safe_dump(config), encoding="utf-8")
    payload = []
    for record in records:
        record = dict(record)
        if german:
            record.setdefault("name_de", f"Deutsch {record['name']}")
        record.setdefault("name_en", f"English {record['name']}")
        payload.append(record)
    (directory / "records.yml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    return directory / "config.yaml"


def codes(config: Path, *, severity: str = "error") -> set[str]:
    return {
        issue.code
        for issue in check_kb_package(config, package_kinds={}).issues
        if issue.severity == severity
    }


def reporting(
    root: Path,
    validators: list[str],
    *,
    kind: str = "report_templates",
    extra: tuple[dict[str, object], ...] = (),
) -> Path:
    return module(
        root,
        "reporting",
        [
            {
                "model": "report_template_section",
                "name": "section",
                "findings": ["lesion"],
            },
            {
                "model": "report_template",
                "name": "template",
                "examination": "exam",
                "report_sections": ["section"],
                "validators": {"findings_validators": validators},
            },
            *extra,
        ],
        kind=kind,
        depends_on=("terms",),
    )


VALIDATOR = {
    "model": "findings_validator",
    "name": "lesion_present",
    "finding": "lesion",
    "operator": "exists",
}


def test_valid_declared_packages_have_no_errors(tmp_path: Path) -> None:
    module(tmp_path, "terms", [*TERMS, VALIDATOR], kind="terminology")
    config = reporting(tmp_path, ["lesion_present"])
    assert codes(config) == set()


def test_invalid_package_kind_is_an_error(tmp_path: Path) -> None:
    config = module(tmp_path, "terms", TERMS, kind="concepts")
    assert "invalid_package_kind" in codes(config)


@pytest.mark.parametrize(
    "change",
    [{"package_kind": "report_templates"}, {"version": "2.0.0"}, {"name": "other"}],
)
def test_root_manifest_disagreeing_with_config_is_an_error(
    tmp_path: Path, change: dict[str, str]
) -> None:
    config = module(tmp_path, "terms", TERMS, kind="terminology")
    manifest = {
        "schema": "lx-package/1",
        "name": "terms",
        "version": "1.0.0",
        "package_kind": "terminology",
    }
    (config.parent / "lx-package.json").write_text(json.dumps(manifest))
    assert "package_manifest_mismatch" not in codes(config)
    (config.parent / "lx-package.json").write_text(json.dumps({**manifest, **change}))
    assert "package_manifest_mismatch" in codes(config)


def test_kind_dependency_violation_requires_both_kinds(tmp_path: Path) -> None:
    module(tmp_path, "terms", TERMS, kind="study")
    config = reporting(tmp_path, [])
    assert "package_kind_dependency_violation" in codes(config)
    (tmp_path / "terms" / "config.yaml").write_text(
        (tmp_path / "terms" / "config.yaml")
        .read_text()
        .replace("package_kind: study\n", "")
    )
    clear_knowledge_base_resolver_caches()
    assert "package_kind_dependency_violation" not in codes(config)


def test_application_data_dependency_is_allowed(tmp_path: Path) -> None:
    module(tmp_path, "terms", TERMS, kind="application_data")
    config = reporting(tmp_path, [])
    assert "package_kind_dependency_violation" not in codes(config)


def test_reviewed_kind_conflicting_with_declaration_is_an_error(tmp_path: Path) -> None:
    config = module(tmp_path, "terms", TERMS, kind="terminology")
    result = check_kb_package(
        config, package_kinds={("terms", "1.0.0"): PackageKind.study}
    )
    assert "package_kind_conflict" in {issue.code for issue in result.issues}


@pytest.mark.parametrize("kind", ["study", "application_data"])
def test_validators_in_study_or_application_data_are_errors(
    tmp_path: Path, kind: str
) -> None:
    config = module(tmp_path, "terms", [*TERMS, VALIDATOR], kind=kind)
    assert "validators_in_package_kind" in codes(config)


def test_unresolved_and_duplicate_template_validators_are_errors(
    tmp_path: Path,
) -> None:
    module(tmp_path / "a", "terms", [*TERMS, VALIDATOR], kind="terminology")
    unresolved = reporting(tmp_path / "a", ["not_defined"])
    assert "unknown_findings_validator_reference" in codes(unresolved)
    module(tmp_path / "b", "terms", [*TERMS, VALIDATOR], kind="terminology")
    duplicate = reporting(
        tmp_path / "b",
        ["lesion_present"],
        extra=({**VALIDATOR, "operator": "missing"},),
    )
    assert "duplicate_name" in codes(duplicate)


@pytest.mark.parametrize(
    "name_de",
    [None, "", "  ", "lesion"],
    ids=["missing", "empty", "blank", "identifier"],
)
def test_german_name_must_be_authored(tmp_path: Path, name_de: str | None) -> None:
    finding: dict[str, object] = {**TERMS[0]}
    if name_de is not None:
        finding["name_de"] = name_de
    config = module(
        tmp_path,
        "terms",
        [finding, {**TERMS[1], "name_de": "Untersuchung"}],
        german=False,
    )
    assert "missing_german_name" in codes(config)


def test_german_name_applies_to_sections_templates_and_validators(
    tmp_path: Path,
) -> None:
    module(tmp_path, "terms", [*TERMS, VALIDATOR], kind="terminology")
    config = reporting(tmp_path, ["lesion_present"])
    records = yaml.safe_load((config.parent / "records.yml").read_text())
    records[0]["name_de"] = "section"
    records[1]["name_de"] = ""
    (config.parent / "records.yml").write_text(yaml.safe_dump(records))
    messages = [
        issue.message
        for issue in check_kb_package(config, package_kinds={}).issues
        if issue.code == "missing_german_name"
    ]
    assert len(messages) == 2
    assert any("'report_template_section' 'section'" in m for m in messages)
    assert any("'report_template' 'template'" in m for m in messages)


def test_cli_surfaces_kind_codes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config = module(tmp_path, "terms", TERMS, kind="concepts")
    monkeypatch.setattr("sys.argv", ["ok", "--config", str(config)])
    assert cli.main() == 1
    assert "invalid_package_kind" in capsys.readouterr().out


def test_shipped_package_without_kind_is_an_error() -> None:
    descriptor = get_packaged_knowledge_base("polyp_size_category", "2.0.0")
    catalog = PackagedKnowledgeBaseCatalog(
        schema_version=1,
        knowledge_bases=(descriptor.model_copy(update={"package_kind": None}),),
    )
    result = check_packaged_knowledge_bases(catalog)[("polyp_size_category", "2.0.0")]
    assert "unclassified_shipped_package" in {issue.code for issue in result.issues}


def test_active_packages_pass_and_archived_clinical_copies_are_rejected() -> None:
    results = check_packaged_knowledge_bases()
    catalog = get_packaged_knowledge_base_catalog()
    assert set(results) == {
        (item.module_name, item.version) for item in catalog.knowledge_bases
    }
    for item in catalog.knowledge_bases:
        result = results[(item.module_name, item.version)]
        errors = [issue for issue in result.issues if issue.severity == "error"]
        # Published legacy bytes remain inspectable, never lint-exempt. The
        # active application release must pass the same ownership gate.
        if item.module_name == "endoreg_reference" and not item.default:
            assert {issue.code for issue in errors} == {
                "package_kind_content_violation"
            }
        else:
            assert errors == [], [issue.format() for issue in errors]
    assert all(result.knowledge_base is not None for result in results.values())


# --- Package kinds stay separate: own records must belong to the kind --------

PROFESSION_CATALOG = {
    "model": "reference_catalog",
    "name": "profession",
    "payload": {
        "schema_version": "1.0",
        "records": [
            {"record_type": "profession", "name": "nurse", "description": "Nurse"}
        ],
    },
}
FINDING_CATALOG = {
    "model": "reference_catalog",
    "name": "finding",
    "payload": {
        "schema_version": "1.0",
        "records": [
            {
                "record_type": "finding",
                "name": "lesion",
                "description": None,
                "finding_types": [],
                "finding_interventions": [],
                "caused_by_interventions": [],
                "finding_classifications": [],
                "information_sources": [],
            }
        ],
    },
}


def test_application_data_with_its_own_catalogs_is_separate(tmp_path: Path) -> None:
    config = module(
        tmp_path, "workforce", [PROFESSION_CATALOG], kind="application_data"
    )
    assert "package_kind_content_violation" not in codes(config)


def test_application_data_may_not_carry_terminology_in_catalogs(
    tmp_path: Path,
) -> None:
    config = module(tmp_path, "reference", [FINDING_CATALOG], kind="application_data")
    result = check_kb_package(config, package_kinds={})
    issue = next(
        issue
        for issue in result.issues
        if issue.code == "package_kind_content_violation"
    )
    assert issue.severity == "error"
    assert "finding" in issue.message


@pytest.mark.parametrize(
    ("kind", "records"),
    [
        ("terminology", [*TERMS, PROFESSION_CATALOG]),
        ("application_data", [*TERMS]),
        ("study", [*TERMS]),
    ],
)
def test_own_records_outside_the_declared_kind_are_errors(
    tmp_path: Path, kind: str, records: list[dict[str, object]]
) -> None:
    config = module(tmp_path, "mixed", records, kind=kind)
    assert "package_kind_content_violation" in codes(config)


@pytest.mark.parametrize(
    "records",
    [[FINDING_CATALOG], [*TERMS, PROFESSION_CATALOG]],
    ids=["terminology-in-catalog", "mixed-kinds"],
)
def test_omitting_package_kind_never_bypasses_the_boundary(
    tmp_path: Path, records: list[dict[str, object]]
) -> None:
    config = module(tmp_path, "undeclared", records, kind=None)
    assert "package_kind_content_violation" in codes(config)


def test_undeclared_single_kind_package_passes(tmp_path: Path) -> None:
    config = module(tmp_path, "undeclared", [PROFESSION_CATALOG], kind=None)
    assert "package_kind_content_violation" not in codes(config)
