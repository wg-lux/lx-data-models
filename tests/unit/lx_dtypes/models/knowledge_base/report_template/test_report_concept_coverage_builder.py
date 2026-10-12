from typing import Any

import pytest

from lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverageBuilder import (
    _concept_status_and_evidence,
    _indexed_mappings,
    _path_value,
    _selected_finding_values,
    _values_validation_status,
    build_report_concept_coverage,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
    ReportTemplateCoverageFindingSelector,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination


class _Config:
    def model_dump(self, *, mode: str) -> dict[str, str]:
        assert mode == "json"
        return {"name": "module", "version": "1.0.0"}


class _KnowledgeBase:
    config = _Config()

    def model_dump(self, *, mode: str) -> dict[str, Any]:
        assert mode == "json"
        return {"config": {"name": "module", "version": "1.0.0"}}


def _payload() -> PExamination:
    return PExamination.model_validate(
        {
            "patient": "p",
            "examination": "exam",
            "patient_findings": [{"finding": "polyp", "patient_examination": "p-exam"}],
        }
    )


def _template() -> dict[str, Any]:
    return {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "present.concept",
                "label": "Present",
                "applicability_status": "required",
                "validator_names": ["present_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["polyp"],
            },
            {
                "concept_id": "missing.concept",
                "label": "Missing",
                "applicability_status": "required",
                "validator_names": ["missing_validator"],
                "evidence_path": ["patient_findings", "1"],
                "concept_value_path": ["patient_findings", "1", "finding"],
                "allowed_values": ["mass"],
            },
            {
                "concept_id": "conditional.concept",
                "label": "Conditional",
                "applicability_status": "conditional",
                "applicability_rule": "context.requires_conditional",
                "validator_names": ["conditional_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["polyp"],
            },
            {
                "concept_id": "not_applicable.concept",
                "label": "Not applicable",
                "applicability_status": "not_applicable",
                "applicability_reason": "Not in this examination",
                "validator_names": ["not_applicable_validator"],
                "evidence_path": ["patient_findings"],
            },
            {
                "concept_id": "invalid.concept",
                "label": "Invalid",
                "applicability_status": "required",
                "validator_names": ["invalid_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "finding"],
                "allowed_values": ["mass"],
            },
            {
                "concept_id": "unknown.concept",
                "label": "Unknown",
                "applicability_status": "required",
                "validator_names": ["unknown_validator"],
                "evidence_path": ["patient_findings"],
                "concept_value_path": ["patient_findings", "0", "missing_field"],
                "allowed_values": ["polyp"],
            },
        ],
    }


def test_builder_emits_runtime_statuses_and_identity() -> None:
    validation = {
        "findings_validators": [
            {"name": "present_validator", "ok": True, "issues": []},
            {
                "name": "missing_validator",
                "ok": False,
                "issues": [{"code": "finding_not_present"}],
            },
            {"name": "conditional_validator", "ok": True, "issues": []},
            {"name": "not_applicable_validator", "ok": True, "issues": []},
            {
                "name": "invalid_validator",
                "ok": False,
                "issues": [{"code": "bad_value"}],
            },
        ],
        "classification_validators": [],
        "intervention_validators": [],
        "examination_validators": [],
        "unit_validators": [],
    }
    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=_template(),
        p_examination=_payload(),
        validation=validation,
    )
    assert [item.validation_status for item in coverage.concepts] == [
        "present",
        "missing",
        "present",
        "undetermined",
        "invalid",
        "unknown",
    ]
    assert coverage.identity.template_version == "2.0.0"


def test_builder_rejects_template_identity_mismatch() -> None:
    with pytest.raises(ValueError, match="identity"):
        build_report_concept_coverage(
            kb=_KnowledgeBase(),
            requested_template_name="other-template",
            template_export=_template(),
            p_examination=_payload(),
            validation={
                "findings_validators": [],
                "classification_validators": [],
                "intervention_validators": [],
                "examination_validators": [],
                "unit_validators": [],
            },
        )


def test_builder_rejects_lexical_template_without_coverage_metadata() -> None:
    template = _template()
    template.pop("coverage_concepts")
    with pytest.raises(ValueError, match="stable concept IDs"):
        build_report_concept_coverage(
            kb=_KnowledgeBase(),
            requested_template_name="template",
            template_export=template,
            p_examination=_payload(),
            validation={
                "findings_validators": [],
                "classification_validators": [],
                "intervention_validators": [],
                "examination_validators": [],
                "unit_validators": [],
            },
        )


@pytest.mark.parametrize(
    ("value", "value_path", "expected"),
    [
        ("polyp", ["patient_findings", "0", "finding"], "present"),
        ("mass", ["patient_findings", "0", "finding"], "invalid"),
        ("polyp", ["patient_findings", "0", "missing_field"], "unknown"),
    ],
)
def test_builder_semantically_checks_value(
    value: str, value_path: list[str], expected: str
) -> None:
    payload = _payload().model_dump(mode="json")
    payload["patient_findings"][0]["finding"] = value
    template = {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "finding.value",
                "label": "Finding value",
                "applicability_status": "required",
                "validator_names": ["finding_validator"],
                "evidence_path": ["patient_findings", "0"],
                "concept_value_path": value_path,
                "allowed_values": ["polyp"],
            }
        ],
    }
    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=template,
        p_examination=PExamination.model_validate(payload),
        validation={
            "findings_validators": [{"name": "finding_validator", "ok": True}],
            "classification_validators": [],
            "intervention_validators": [],
            "examination_validators": [],
            "unit_validators": [],
        },
    )
    assert coverage.concepts[0].validation_status == expected


def test_not_applicable_does_not_require_value_rule() -> None:
    concept = ReportTemplateCoverageConcept.model_validate(
        {
            "concept_id": "not.applicable",
            "label": "Not applicable",
            "applicability_status": "not_applicable",
            "applicability_reason": "Not present in this examination",
            "validator_names": ["validator"],
            "evidence_path": ["patient_findings"],
        }
    )
    assert concept.concept_value_path is None


def _selector_template() -> dict[str, Any]:
    return {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "lesion.value",
                "label": "Lesion value",
                "applicability_status": "required",
                "validator_names": ["finding_validator"],
                "evidence_path": ["patient_findings"],
                "finding_selector": {
                    "finding_name": "lesion",
                    "classification_name": "severity",
                },
                "allowed_values": ["confirmed"],
            }
        ],
    }


def _selector_coverage(findings: list[dict[str, Any]]) -> Any:
    payload = {
        "patient": "p",
        "examination": "exam",
        "patient_findings": findings,
    }
    return build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=_selector_template(),
        p_examination=PExamination.model_validate(payload),
        validation={
            "findings_validators": [{"name": "finding_validator", "ok": True}],
            "classification_validators": [],
            "intervention_validators": [],
            "examination_validators": [],
            "unit_validators": [],
        },
    )


def _finding_with_choice(choice: str) -> dict[str, Any]:
    return {
        "finding": "lesion",
        "patient_examination": "p-exam",
        "patient_finding_classifications": [
            {
                "patient_finding": "finding-id",
                "patient_finding_classification_choices": [
                    {
                        "classification": "severity",
                        "classification_choice": choice,
                        "patient_finding_classifications": "classification-id",
                    }
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    ("findings", "expected_status", "expected_paths"),
    [
        ([], "missing", ()),
        (
            [_finding_with_choice("confirmed")],
            "present",
            (
                (
                    "patient_findings",
                    "0",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
        (
            [
                {"finding": "other", "patient_examination": "p-exam"},
                _finding_with_choice("confirmed"),
                _finding_with_choice("confirmed"),
            ],
            "present",
            (
                (
                    "patient_findings",
                    "1",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
                (
                    "patient_findings",
                    "2",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
        (
            [{"finding": "lesion", "patient_examination": "p-exam"}],
            "unknown",
            (("patient_findings", "0", "patient_finding_classifications"),),
        ),
        (
            [_finding_with_choice("uncertain")],
            "invalid",
            (
                (
                    "patient_findings",
                    "0",
                    "patient_finding_classifications",
                    "0",
                    "patient_finding_classification_choices",
                    "0",
                ),
            ),
        ),
    ],
)
def test_finding_selector_resolves_all_instances(
    findings: list[dict[str, Any]],
    expected_status: str,
    expected_paths: tuple[tuple[str, ...], ...],
) -> None:
    coverage = _selector_coverage(findings)
    item = coverage.concepts[0]
    assert item.validation_status == expected_status
    assert item.evidence_paths == expected_paths


def test_finding_selector_does_not_hide_invalid_later_instance() -> None:
    findings = [
        _finding_with_choice("confirmed"),
        _finding_with_choice("uncertain"),
    ]
    coverage = _selector_coverage(findings)
    assert coverage.concepts[0].validation_status == "invalid"
    assert coverage.concepts[0].evidence_paths == (
        (
            "patient_findings",
            "0",
            "patient_finding_classifications",
            "0",
            "patient_finding_classification_choices",
            "0",
        ),
        (
            "patient_findings",
            "1",
            "patient_finding_classifications",
            "0",
            "patient_finding_classification_choices",
            "0",
        ),
    )


def test_finding_selector_rejects_choice_without_classification_name() -> None:
    with pytest.raises(ValueError, match="classification_name"):
        ReportTemplateCoverageConcept.model_validate(
            {
                "concept_id": "invalid.selector",
                "label": "Invalid selector",
                "applicability_status": "required",
                "validator_names": ["validator"],
                "evidence_path": ["patient_findings"],
                "finding_selector": {
                    "finding_name": "lesion",
                    "classification_choice": "confirmed",
                },
                "allowed_values": ["confirmed"],
            }
        )


@pytest.mark.parametrize(
    ("examiners", "expected_status"),
    [(["examiner-1"], "present"), ([], "invalid"), ([""], "invalid")],
)
def test_typed_open_identifier_list_constraint(
    examiners: list[str],
    expected_status: str,
) -> None:
    payload = PExamination.model_validate(
        {
            "patient": "p",
            "examination": "exam",
            "examiners": examiners,
        }
    )
    template = {
        "name": "template",
        "version": "2.0.0",
        "coverage_version": "report_concept_coverage_v1",
        "coverage_concepts": [
            {
                "concept_id": "examination.examiners",
                "label": "Examiners",
                "applicability_status": "required",
                "evidence_path": ["examiners"],
                "concept_value_path": ["examiners"],
                "value_constraint": "non_empty_string_list",
                "guideline_citations": ["AWMF-021-022 Statement 2.36"],
            }
        ],
    }
    validation = {
        "findings_validators": [],
        "classification_validators": [],
        "intervention_validators": [],
        "examination_validators": [],
        "unit_validators": [],
    }

    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=template,
        p_examination=payload,
        validation=validation,
    )

    assert coverage.concepts[0].validation_status == expected_status


@pytest.mark.parametrize(
    ("payload", "path", "expected"),
    [
        ({"value": None}, ("value",), (True, None)),
        ({}, ("value",), (False, None)),
        ({"0": "mapped"}, ("0",), (True, "mapped")),
        ({"rows": [{"value": False}]}, ("rows", "0", "value"), (True, False)),
        (["first", "last"], ("-1",), (True, "last")),
        (("first",), ("0",), (True, "first")),
        (bytearray(b"a"), ("0",), (True, 97)),
        ([], ("0",), (False, None)),
        ([1], ("bad",), (False, None)),
        ([1], ("-2",), (False, None)),
        ("text", ("0",), (False, None)),
        (b"text", ("0",), (False, None)),
        (None, ("value",), (False, None)),
        ({"root": 1}, (), (True, {"root": 1})),
    ],
)
def test_path_value_preserves_lookup_semantics(
    payload: object, path: tuple[str, ...], expected: tuple[bool, object]
) -> None:
    result = _path_value(payload, path)

    assert result == expected


@pytest.mark.parametrize("use_selector", [False, True])
@pytest.mark.parametrize(
    ("values", "validator_ok", "validator_missing", "expected"),
    [
        (["polyp"], True, False, "present"),
        (["mass"], True, False, "invalid"),
        (["polyp"], True, True, "unknown"),
        ([], False, True, "unknown"),
        ([], False, False, "missing"),
    ],
)
def test_builder_status_and_evidence_precedence(
    use_selector: bool,
    values: list[str],
    validator_ok: bool,
    validator_missing: bool,
    expected: str,
) -> None:
    template = _template()
    concept = template["coverage_concepts"][0]
    template["coverage_concepts"] = [concept]
    concept["evidence_path"] = ["patient_findings", "0"]
    concept["concept_value_path"] = ["patient_findings", "0", "patient_examination"]
    if use_selector:
        concept["finding_selector"] = {"finding_name": "polyp"}
        concept["concept_value_path"] = ["patient_examination"]
    payload = PExamination.model_validate(
        {
            "patient": "p",
            "examination": "exam",
            "patient_findings": [
                {"finding": "polyp", "patient_examination": value} for value in values
            ],
        }
    )
    validation = {
        "findings_validators": []
        if validator_missing
        else [{"name": "present_validator", "ok": validator_ok}]
    }

    coverage = build_report_concept_coverage(
        kb=_KnowledgeBase(),
        requested_template_name="template",
        template_export=template,
        p_examination=payload,
        validation=validation,
    )

    item = coverage.concepts[0]
    assert item.validation_status == expected
    assert item.evidence_path == ("patient_findings", "0")
    assert item.evidence_paths == (
        ()
        if use_selector and not values and not validator_missing
        else (("patient_findings", "0"),)
    )


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([], "missing"),
        ([(False, "polyp")], "unknown"),
        ([(True, None)], "unknown"),
        ([(True, "polyp")], "present"),
        ([(True, "mass")], "invalid"),
        ([(True, True)], "invalid"),
        ([(True, [])], "invalid"),
        ([(True, ["polyp", "polyp"])], "present"),
        ([(True, ["polyp", "mass"])], "invalid"),
        ([(True, "mass"), (False, None)], "unknown"),
        ([(True, "mass"), (True, {"value": "polyp"})], "unknown"),
        ([(True, "polyp"), (True, "mass")], "invalid"),
    ],
)
def test_values_validation_status(
    values: list[tuple[bool, object]], expected: str
) -> None:
    concept = ReportTemplateCoverageConcept.model_validate(
        _template()["coverage_concepts"][0]
    )

    status = _values_validation_status(values, concept)

    assert status == expected


@pytest.mark.parametrize("use_selector", [False, True])
@pytest.mark.parametrize(
    ("value_path", "expected_direct", "expected_selected"),
    [
        (["finding"], "invalid", "present"),
        (["absent"], "invalid", "unknown"),
    ],
)
def test_failed_validator_precedence_depends_on_selector(
    use_selector: bool,
    value_path: list[str],
    expected_direct: str,
    expected_selected: str,
) -> None:
    data = _template()["coverage_concepts"][0]
    if use_selector:
        data["finding_selector"] = {"finding_name": "polyp"}
        data["concept_value_path"] = value_path
    else:
        data["concept_value_path"] = ["patient_findings", "0", *value_path]
    concept = ReportTemplateCoverageConcept.model_validate(data)
    payload = {"patient_findings": [{"finding": "polyp"}]}
    validators = {"present_validator": {"ok": False}}

    result = _concept_status_and_evidence(payload, concept, validators)

    assert result == (
        expected_selected if use_selector else expected_direct,
        (("patient_findings", "0"),) if use_selector else (("patient_findings",),),
    )


@pytest.mark.parametrize(
    "malformed", [None, 1, "text", b"bytes", bytearray(b"x"), {}, [None], ()]
)
@pytest.mark.parametrize("level", ["findings", "classifications", "choices"])
def test_selector_malformed_containers_preserve_missing_evidence(
    malformed: object, level: str
) -> None:
    classifications = "patient_finding_classifications"
    choices = "patient_finding_classification_choices"
    finding: dict[str, object] = {"finding": "lesion"}
    payload: dict[str, object] = {"patient_findings": [finding]}
    if level == "findings":
        payload["patient_findings"] = malformed
    elif level == "classifications":
        finding[classifications] = malformed
    else:
        finding[classifications] = [{choices: malformed}]
    selector = ReportTemplateCoverageFindingSelector(
        finding_name="lesion", classification_name="severity"
    )

    result = _selected_finding_values(payload, selector, None)

    assert result == (
        []
        if level == "findings"
        else [(("patient_findings", "0", classifications), False, None)]
    )


@pytest.mark.parametrize("choice_filter", [None, "confirmed", "absent"])
@pytest.mark.parametrize("value_path", [None, [], ["detail", "value"], ["absent"]])
def test_selector_preserves_indices_filters_and_relative_values(
    choice_filter: str | None, value_path: list[str] | None
) -> None:
    classifications = "patient_finding_classifications"
    choices = "patient_finding_classification_choices"
    finding = {
        "finding": "lesion",
        classifications: [
            None,
            {
                choices: (
                    None,
                    {"classification": "other"},
                    {
                        "classification": "severity",
                        "classification_choice": "confirmed",
                        "detail": {"value": 0},
                    },
                )
            },
            {
                choices: [
                    {"classification": "severity", "classification_choice": "uncertain"}
                ]
            },
        ],
    }
    payload = {"patient_findings": (None, {"finding": "other"}, finding, finding)}
    selector = ReportTemplateCoverageFindingSelector(
        finding_name="lesion",
        classification_name="severity",
        classification_choice=choice_filter,
    )
    expected: list[tuple[tuple[str, ...], bool, object]] = []
    for index in ("2", "3"):
        path = ("patient_findings", index, classifications)
        if choice_filter == "absent":
            expected.append((path, False, None))
            continue
        exists, value = (
            (False, None)
            if value_path == ["absent"]
            else (True, 0)
            if value_path
            else (True, "confirmed")
        )
        expected.append((path + ("1", choices, "2"), exists, value))
        if choice_filter is None:
            expected.append(
                (
                    path + ("2", choices, "0"),
                    not bool(value_path),
                    None if value_path else "uncertain",
                )
            )

    result = _selected_finding_values(payload, selector, value_path)

    assert result == expected


@pytest.mark.parametrize(
    "choice",
    [
        {"classification": "severity"},
        {
            "classification": "severity",
            "classification_choice": None,
        },
    ],
)
def test_selector_distinguishes_missing_choice_from_null(
    choice: dict[str, object],
) -> None:
    payload = {
        "patient_findings": [
            {
                "finding": "lesion",
                "patient_finding_classifications": [
                    {"patient_finding_classification_choices": [choice]}
                ],
            }
        ]
    }
    selector = ReportTemplateCoverageFindingSelector(
        finding_name="lesion", classification_name="severity"
    )

    result = _selected_finding_values(payload, selector, None)

    assert result == [
        (
            (
                "patient_findings",
                "0",
                "patient_finding_classifications",
                "0",
                "patient_finding_classification_choices",
                "0",
            ),
            "classification_choice" in choice,
            None,
        )
    ]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, []),
        ("text", []),
        (b"bytes", []),
        ({"finding": "lesion"}, []),
        ([], []),
        (
            [None, {}, "skip", {"finding": "lesion"}],
            [(1, {}), (3, {"finding": "lesion"})],
        ),
        ((False, {"finding": "lesion"}), [(1, {"finding": "lesion"})]),
    ],
)
def test_indexed_mappings_preserves_original_positions(
    value: object, expected: list[tuple[int, dict[str, str]]]
) -> None:
    result = list(_indexed_mappings(value))

    assert result == expected


@pytest.mark.parametrize("path", [None, [], ["finding"], ["absent"]])
def test_selector_without_classification_resolves_relative_path(
    path: list[str] | None,
) -> None:
    finding = {"finding": "lesion"}
    payload = {"patient_findings": [None, finding]}
    selector = ReportTemplateCoverageFindingSelector(finding_name="lesion")
    expected = (
        (False, None) if path == ["absent"] else (True, "lesion" if path else finding)
    )

    result = _selected_finding_values(payload, selector, path)

    assert result == [(("patient_findings", "1"), *expected)]
