from copy import deepcopy
from string import Formatter
from typing import Literal

import pytest

from lx_dtypes.language import LANGUAGE_LABELS, load_message_catalogue
from lx_dtypes.models.knowledge_base.report_template import ValidatorRuntime as runtime
from lx_dtypes.models.knowledge_base.report_template.ClassificationValidator import (
    ClassificationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.report_template.FindingsValidator import (
    FindingsValidator,
)
from lx_dtypes.models.knowledge_base.report_template.InterventionValidator import (
    InterventionValidator,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.report_template.UnitValidator import UnitValidator


@pytest.mark.parametrize(
    "filename", ["validator_runtime_messages.yml", "validation_messages.yml"]
)
def test_message_catalogue_has_matching_languages_and_placeholders(
    filename: str,
) -> None:
    messages = load_message_catalogue(filename)
    assert messages.keys() == LANGUAGE_LABELS.keys()
    assert messages["de"].keys() == messages["en"].keys()
    formatter = Formatter()
    for key, german in messages["de"].items():
        english = messages["en"][key]
        assert german != english
        assert {field for _, field, _, _ in formatter.parse(german) if field} == {
            field for _, field, _, _ in formatter.parse(english) if field
        }


@pytest.mark.parametrize("kind", ["finding", "classification", "intervention", "unit"])
def test_atomic_validator_language_changes_only_messages(kind: str) -> None:
    values = {"name": "rule", "finding": "polyp", "operator": "exists"}

    def evaluate(language: runtime.RuntimeValidationLanguage):
        if kind == "finding":
            return runtime.evaluate_findings_validator_runtime(
                FindingsValidator.model_validate(values), language=language
            )
        if kind == "classification":
            return runtime.evaluate_classification_validator_runtime(
                ClassificationValidator.model_validate(
                    {**values, "classification": "size"}
                ),
                classifications={},
                classification_choices={},
                classification_choice_descriptors={},
                language=language,
            )
        if kind == "intervention":
            return runtime.evaluate_intervention_validator_runtime(
                InterventionValidator.model_validate(
                    {**values, "intervention": "resection"}
                ),
                interventions={},
                language=language,
            )
        return runtime.evaluate_unit_validator_runtime(
            UnitValidator.model_validate(
                {**values, "classification": "size", "unit": "mm"}
            ),
            units={},
            language=language,
        )

    german, english = evaluate("de"), evaluate("en")
    assert german["ok"] is english["ok"] is False
    assert german["issues"][0]["message"] != english["issues"][0]["message"]
    assert "rule" in german["issues"][0]["message"]
    german["issues"][0]["message"] = english["issues"][0]["message"]
    assert german == english


def test_default_is_german_and_english_wording_is_preserved() -> None:
    validator = FindingsValidator(name="rule", finding="polyp", operator="exists")
    default = runtime.evaluate_findings_validator_runtime(validator)
    english = runtime.evaluate_findings_validator_runtime(validator, language="en")
    assert default["issues"][0]["message"] == (
        "Befund 'polyp' wird von Prüfregel 'rule' benötigt, ist aber nicht vorhanden."
    )
    assert english["issues"][0]["message"] == (
        "Finding 'polyp' is required by validator 'rule' but is not present."
    )
    with pytest.raises(ValueError, match="language"):
        runtime.evaluate_findings_validator_runtime(
            validator,
            reported_findings=[{"finding": "polyp"}],
            language="fr",  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("language", ["de", "en"])
def test_template_dependency_and_cycle_messages_use_selected_language(
    language: Literal["de", "en"],
) -> None:
    template = ReportTemplate.model_validate(
        {
            "name": "template",
            "examination": "colonoscopy",
            "report_sections": [],
            "validators": {
                "examination_validators": ["exam"],
                "classification_validators": ["unknown"],
            },
        }
    )
    result = runtime.evaluate_report_template_validators_runtime(
        template,
        classification_validators={},
        intervention_validators={},
        unit_validators={},
        classifications={},
        classification_choices={},
        classification_choice_descriptors={},
        interventions={},
        units={},
        findings_validators={
            "rule": FindingsValidator(name="rule", finding="polyp", operator="exists")
        },
        examination_validators={
            "exam": ExaminationValidator.model_validate(
                {
                    "name": "exam",
                    "finding_validators": ["rule"],
                    "examination_validators": ["exam"],
                }
            )
        },
        language=language,
    )
    assert result["ok"] is False
    assert {issue["code"] for issue in result["issues"]} == {
        "unknown_classification_validator_reference",
        "finding_not_present",
        "failed_finding_validator_dependency",
        "failed_examination_validator_dependency",
        "circular_examination_validator_dependency",
    }
    for issue in result["issues"]:
        assert (
            ("Prüfregel" in issue["message"] or "prüfregel" in issue["message"])
            if language == "de"
            else "validator" in issue["message"]
        )


def test_missing_condition_data_is_localized_without_changing_details() -> None:
    validator = FindingsValidator.model_validate(
        {
            "name": "conditional",
            "finding": "polyp",
            "query": {
                "operator": "condition",
                "condition": {
                    "all": [
                        {"classification": "size", "comparator": "gt", "value": 10}
                    ],
                    "then_requires": [{"kind": "classification", "name": "location"}],
                },
            },
        }
    )
    findings: list[dict[str, object]] = [{"finding": "polyp"}]
    german = runtime.evaluate_findings_validator_runtime(
        validator, reported_findings=findings
    )
    english = runtime.evaluate_findings_validator_runtime(
        validator, language="en", reported_findings=findings
    )
    assert german["issues"][0]["code"] == "missing_data_requirement"
    assert "Ausgangsdaten fehlen: size" in german["issues"][0]["message"]
    comparable = deepcopy(german)
    comparable["issues"][0]["message"] = english["issues"][0]["message"]
    assert comparable == english
