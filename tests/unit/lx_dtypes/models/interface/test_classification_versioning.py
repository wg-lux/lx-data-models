from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.knowledge_bases import list_packaged_knowledge_bases
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.numeric_classification import (
    NumericClassificationRules,
    NumericMeasurement,
)
from lx_dtypes.models.interface.examples import build_star_upper_gi_demo_interface
from lx_dtypes.models.interface.examples.demo_classification_versioning import (
    run_comparison,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseVersionNotFoundError,
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
)
from lx_dtypes.numeric_classification import (
    classify_measurement,
    load_numeric_classification,
    read_rules,
    validate_measurement_source,
)

ROOT = Path(__file__).resolve().parents[5]


@pytest.fixture(autouse=True)
def registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    modules: dict[str, dict[str, object]] = {}
    for item in list_packaged_knowledge_bases():
        modules.setdefault(item.module_name, {})[item.version] = {
            "sources": [
                {
                    "kind": "provider",
                    "provider": "lx_dtypes.builtin",
                    "content_sha256": item.content_sha256,
                }
            ]
        }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps({"modules": modules}))
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(path))
    clear_knowledge_base_resolver_caches()


def measurement(value: float = 6.0, **changes: object) -> NumericMeasurement:
    return NumericMeasurement.model_validate(
        {
            "observation_id": "synthetic-1",
            "value": value,
            "source_knowledge_base": {
                "knowledge_base_module": "star_upper_gi",
                "knowledge_base_version": "0.1.1.post1",
            },
            "descriptor": "length_mm_descriptor",
            "unit": "millimeter",
            **changes,
        }
    )


def test_table4_through_registry_preserves_sources() -> None:
    results = run_comparison(
        ROOT / "demo-data/classification_versioning/measurements.yml"
    )
    assert len(results) == 10
    for old, new in zip(results[:5], results[5:], strict=True):
        assert old.measurement == new.measurement
        assert (
            old.knowledge_base.knowledge_base_module
            == new.knowledge_base.knowledge_base_module
        )
        assert old.knowledge_base.knowledge_base_version == "1.0.0"
        assert new.knowledge_base.knowledge_base_version == "2.0.0"
        assert old.rules_sha256 != new.rules_sha256
    with pytest.raises(KnowledgeBaseVersionNotFoundError):
        load_numeric_classification("polyp_size_category", version="9.0.0")


@pytest.mark.parametrize(
    ("value", "choice"),
    [
        (1.0, "size_le_5"),
        (5.0, "size_le_5"),
        (6.0, "size_6_9"),
        (9.0, "size_6_9"),
        (10.0, "size_10_19"),
        (19.0, "size_10_19"),
        (20.0, "size_ge_20"),
        (22.0, "size_ge_20"),
    ],
)
def test_revised_boundaries(value: float, choice: str) -> None:
    rules = load_numeric_classification("polyp_size_category", version="2.0.0")
    assert classify_measurement(measurement(value), rules).choice == choice


def test_fractional_policy_is_explicit() -> None:
    old = load_numeric_classification("polyp_size_category", version="1.0.0")
    new = load_numeric_classification("polyp_size_category", version="2.0.0")
    assert classify_measurement(measurement(5.5), old).choice == "size_gt_5"
    for value in (5.5, 9.5, 19.5):
        with pytest.raises(ValueError, match="whole-number"):
            classify_measurement(measurement(value), new)


@pytest.mark.parametrize("value", [True, "6", None, float("inf"), float("nan")])
def test_measurement_rejects_invalid_numeric_values(value: object) -> None:
    with pytest.raises(ValidationError):
        NumericMeasurement.model_validate(
            {**measurement().model_dump(), "value": value}
        )


@pytest.mark.parametrize("value", [0.0, -1.0])
def test_nonpositive_measurements_are_outside_domain(value: float) -> None:
    rules = load_numeric_classification("polyp_size_category", version="1.0.0")
    with pytest.raises(ValueError, match="outside"):
        classify_measurement(measurement(value), rules)


@pytest.mark.parametrize("changes", [{"unit": "centimeter"}, {"descriptor": "other"}])
def test_no_implicit_unit_or_descriptor_conversion(changes: dict[str, object]) -> None:
    rules = load_numeric_classification("polyp_size_category", version="2.0.0")
    with pytest.raises(ValueError, match="differs"):
        classify_measurement(
            NumericMeasurement.model_validate(
                {
                    **measurement().model_dump(),
                    **changes,
                }
            ),
            rules,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lower", 4.0),
        ("lower", 6.0),
        ("lower_inclusive", True),
        ("choice", "size_le_5"),
        ("upper", 100.0),
    ],
)
def test_invalid_partitions_fail(field: str, value: object) -> None:
    rules = load_numeric_classification("polyp_size_category", version="1.0.0")
    payload = json.loads(rules.model_dump_json())
    payload["rules"][1][field] = value
    with pytest.raises(ValidationError):
        NumericClassificationRules.model_validate(payload)


@pytest.mark.parametrize(
    ("before", "after", "message"),
    [
        ("knowledge_base_version: 2.0.0", "knowledge_base_version: 7.0.0", "identity"),
        ("choice: size_6_9", "choice: missing", "choices"),
        ("unit: millimeter", "unit: missing", "unit"),
    ],
)
def test_rules_are_bound_to_resolved_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    before: str,
    after: str,
    message: str,
) -> None:
    root = tmp_path / "bundle"
    shutil.copytree(ROOT / "lx_dtypes/data/polyp_size_category", root)
    path = root / "numeric_rules.yml"
    path.write_text(path.read_text().replace(before, after))
    registry_path = tmp_path / "custom.json"
    registry_path.write_text(
        json.dumps(
            {
                "modules": {
                    "polyp_size_category": {
                        "2.0.0": {
                            "sources": [
                                {"kind": "filesystem", "input_dirs": [str(root)]}
                            ]
                        }
                    }
                }
            }
        )
    )
    monkeypatch.setenv("LX_DTYPES_KB_REGISTRY", str(registry_path))
    with pytest.raises(ValueError, match=message):
        load_numeric_classification("polyp_size_category", version="2.0.0")


def test_duplicate_yaml_rule_keys_fail(tmp_path: Path) -> None:
    path = tmp_path / "rules.yml"
    path.write_text("schema_version: 1\nschema_version: 1\n")
    with pytest.raises(ValueError, match="duplicate"):
        read_rules(path)


def test_repaired_star_snapshot_and_real_ledger_measurements() -> None:
    kb: KnowledgeBase = load_knowledge_base("star_upper_gi", version="0.1.1.post1")
    kb.export_core_concepts()
    assert (len(kb.finding), len(kb.classification), len(kb.classification_choice)) == (
        22,
        21,
        79,
    )
    assert len(kb.classification_choice_descriptor) == 3
    assert len(kb.unit) == 41
    interface = build_star_upper_gi_demo_interface(kb)
    before = interface.model_dump_json()
    rules = load_numeric_classification("polyp_size_category", version="2.0.0")
    values: list[float] = []
    for exam in interface.ledger.patient_examinations.values():
        for finding in exam.patient_findings:
            if finding.finding != "star_upper_gi_polyp":
                continue
            for group in finding.patient_finding_classifications:
                for choice in group.patient_finding_classification_choices:
                    for (
                        descriptor
                    ) in choice.patient_finding_classification_choice_descriptors:
                        if (
                            descriptor.classification_choice_descriptor
                            != "length_mm_descriptor"
                        ):
                            continue
                        observed = NumericMeasurement.model_validate(
                            {
                                **measurement().model_dump(),
                                "observation_id": str(descriptor.uuid),
                                "value": descriptor.descriptor_value,
                            }
                        )
                        validate_measurement_source(observed, kb)
                        assert (
                            classify_measurement(observed, rules).choice == "size_6_9"
                        )
                        values.append(observed.value)
    # The existing ledger has one 8 mm polyp; the 6 mm finding is a diverticulum.
    assert values == [8.0]
    assert interface.model_dump_json() == before
    with pytest.raises(ValueError, match="identity"):
        validate_measurement_source(
            measurement(
                source_knowledge_base=KnowledgeBaseIdentity(
                    knowledge_base_module="star_upper_gi",
                    knowledge_base_version="0.1.2",
                )
            ),
            kb,
        )
