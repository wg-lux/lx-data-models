from __future__ import annotations

import pytest

from lx_dtypes.scripts import verify_packaged_report_templates as verifier_module
from lx_dtypes.scripts.verify_packaged_report_templates import (
    REQUIRED_PACKAGED_REPORT_TEMPLATES,
    verify_packaged_report_templates,
)


def test_multiple_packaged_report_templates_are_published_and_usable() -> None:
    assert verify_packaged_report_templates() == list(
        REQUIRED_PACKAGED_REPORT_TEMPLATES
    )


@pytest.mark.parametrize(
    "module_name",
    [
        "star_upper_gi",
        "dgvs_reporting",
        "coloreg",
        "mst_3_0",
        "report_template_examples",
    ],
)
def test_reporting_catalog_has_german_labels(module_name: str) -> None:
    """Check resolved YAML references, including choices and input descriptors."""
    kb = verifier_module.DataLoader().load_knowledge_base(module_name)

    def assert_label(name: str, label: str | None) -> None:
        assert label and label.strip() and label not in (name, "unknown"), name
        assert "_" not in label, (name, label)

    finding_names: set[str] = set()
    for template_name in kb.report_template:
        if template_name == "base_report_template":
            # This legacy authoring example deliberately has incomplete coverage.
            with pytest.raises(KeyError, match="not production-ready"):
                kb.export_report_template(template_name)
            continue
        exported = kb.export_report_template(template_name)
        assert_label(template_name, exported["name_de"])
        assert exported["verbosity_options"] == ["short", "standard", "detailed"]
        examination = kb.examination[exported["examination"]]
        assert_label(examination.name, examination.name_de)
        for section in exported["report_sections"]:
            assert_label(section["name"], section["title_de"])
            finding_names.update(finding["finding"] for finding in section["findings"])
            for finding in section["findings"]:
                for classification in finding.get("classifications", []):
                    for choice in classification["input"]["choices"]:
                        for descriptor in choice["descriptors"]:
                            assert_label(descriptor["name"], descriptor["name_de"])

    for finding_name in finding_names:
        finding = kb.finding[finding_name]
        assert_label(finding.name, finding.name_de)
        for classification_name in finding.classifications:
            classification = kb.classification[classification_name]
            assert_label(classification.name, classification.name_de)
            for choice_name in classification.classification_choices:
                choice = kb.classification_choice[choice_name]
                assert_label(choice.name, choice.name_de)
                for descriptor_name in choice.classification_choice_descriptors:
                    descriptor = kb.classification_choice_descriptor[descriptor_name]
                    assert_label(descriptor.name, descriptor.name_de)


def test_star_upper_gi_patient_fields_have_german_labels() -> None:
    kb = verifier_module.DataLoader().load_knowledge_base("star_upper_gi")
    fields = kb.export_report_template("star_upper_gi_standard_report_template")[
        "report_sections"
    ][0]["fields"]
    assert [field["label"] for field in fields] == [
        "Patientenname",
        "Geburtsdatum",
        "Untersuchungsdatum",
    ]


def test_packaged_report_template_verifier_requires_multiple_templates() -> None:
    with pytest.raises(ValueError, match="At least two"):
        verify_packaged_report_templates(["upper_gi_quality_2025"])


def test_coloreg_template_exposes_only_conditional_paris_and_nice_polyps() -> None:
    payload = (
        verifier_module.DataLoader()
        .load_knowledge_base("coloreg")
        .export_report_template("coloreg_colonoscopy")
    )

    assert payload["examination"] == "colonoscopy"
    assert payload["version"] == "1.0.0"
    assert payload["readiness"]["lifecycle_status"] == "published"
    assert payload["readiness"]["can_publish"] is True
    assert len(payload["report_sections"]) == 1
    findings = payload["report_sections"][0]["findings"]
    assert len(findings) == 1
    assert findings[0]["finding"] == "colon_polyp"
    assert findings[0]["required"] is False
    assert findings[0]["multiple_allowed"] is True
    assert {
        requirement["classification"]: requirement["required"]
        for requirement in findings[0]["classifications"]
    } == {
        "colon_lesion_paris": True,
        "colon_lesion_nice": True,
    }


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "",
                "report_sections": [{"title_de": "Befund"}],
            },
            "no German title",
        ),
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "Koloskopie",
                "report_sections": [],
            },
            "no report sections",
        ),
        (
            {
                "readiness": {"lifecycle_status": "published", "can_publish": True},
                "name_de": "Koloskopie",
                "report_sections": [{"title_de": ""}],
            },
            "unlabeled German section",
        ),
    ],
)
def test_packaged_report_template_verifier_rejects_incomplete_german_demo(
    monkeypatch: pytest.MonkeyPatch,
    payload: dict[str, object],
    message: str,
) -> None:
    class _KnowledgeBase:
        def export_report_template(self, template_name: str) -> dict[str, object]:
            del template_name
            return payload

    class _Loader:
        def load_knowledge_base(self, module_name: str) -> _KnowledgeBase:
            assert module_name == "report_template_examples"
            return _KnowledgeBase()

    monkeypatch.setattr(verifier_module, "DataLoader", _Loader)

    with pytest.raises(RuntimeError, match=message):
        verify_packaged_report_templates(["template_a", "template_b"])
