"""German rule-evaluation messages show German concept names, never raw identifiers."""

import re
import warnings
from uuid import NAMESPACE_URL, uuid5

import pytest

from lx_dtypes.knowledge_bases import list_packaged_knowledge_bases
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.models.knowledge_base.report_template import (
    ReportTemplate,
    validate_report_template_structure,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.utils.parser import camel_to_snake

TEMPLATE_PACKAGES = [
    item
    for item in list_packaged_knowledge_bases()
    if item.default and item.package_kind is not None
]


def _load(descriptor) -> KnowledgeBase:  # type: ignore[no-untyped-def]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return load_knowledge_base(
            descriptor.module_name,
            version=descriptor.version,
            input_dirs=[descriptor.installed_data_root()],
        )


def _german_names(kb: KnowledgeBase) -> dict[str, str]:
    names: dict[str, str] = {}
    for model in KB_MODEL_NAMES_ORDERED:
        for name, record in getattr(kb, camel_to_snake(model)).items():
            german = (getattr(record, "name_de", "") or "").strip()
            if german and german != name:
                names[name] = german
    return names


def _messages(value: object) -> list[str]:
    if isinstance(value, dict):
        found = [value["message"]] if isinstance(value.get("message"), str) else []
        return found + [m for item in value.values() for m in _messages(item)]
    if isinstance(value, (list, tuple)):
        return [m for item in value for m in _messages(item)]
    return []


def _leaked_identifiers(message: str, names: dict[str, str]) -> set[str]:
    tokens = set(re.findall(r"'([^']+)'", message)) | set(
        re.findall(r"[A-Za-z0-9_]+", message)
    )
    return {token for token in tokens if token in names}


@pytest.mark.parametrize(
    "descriptor",
    TEMPLATE_PACKAGES,
    ids=[f"{item.module_name}@{item.version}" for item in TEMPLATE_PACKAGES],
)
def test_published_templates_with_empty_findings_report_german_names(
    descriptor,  # type: ignore[no-untyped-def]
) -> None:
    kb = _load(descriptor)
    names = _german_names(kb)
    for template_name in kb.published_report_template_names():
        template = kb.report_template[template_name]
        exam = PExamination(
            examination=template.examination,
            patient=str(uuid5(NAMESPACE_URL, "synthetic-patient")),
            uuid=uuid5(NAMESPACE_URL, f"synthetic-{template_name}"),
            **kb.config.knowledge_base_identity.model_dump(),
        )
        result = kb.evaluate_report_template_validators(
            template_name, p_examination=exam, language="de"
        )
        readiness = ReportTemplateValidator(
            kb=kb, compiler=ReportTemplateCompiler(kb=kb)
        ).validate_and_compile(template_name, language="de")
        messages = _messages(result) + [
            issue.message for issue in readiness["summary"].issues
        ]
        leaks = {
            message: _leaked_identifiers(message, names)
            for message in messages
            if _leaked_identifiers(message, names)
        }
        assert leaks == {}, template_name
        # Every runtime entry names its validator and referenced concepts.
        for kind in (
            "findings_validators",
            "classification_validators",
            "intervention_validators",
            "unit_validators",
            "examination_validators",
        ):
            for entry in result[kind]:
                display = entry.get("display_names", {})
                assert entry["name"] in display
                if entry["name"] in names:
                    assert display[entry["name"]] == names[entry["name"]]
        assert result.get("display_names", {})[template_name] == names.get(
            template_name, template_name
        )


def test_structure_and_readiness_messages_are_localised() -> None:
    descriptor = next(
        item for item in TEMPLATE_PACKAGES if item.module_name == "dgvs_reporting"
    )
    kb = _load(descriptor)
    published = kb.report_template[kb.published_report_template_names()[0]]
    broken = ReportTemplate(
        name="synthetic_template",
        name_de="Synthetische Vorlage",
        name_en="Synthetic template",
        examination=published.examination,
        report_sections=["absent_section"],
    )
    german = validate_report_template_structure(
        broken,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
    )
    english = validate_report_template_structure(
        broken,
        sections=kb.report_template_section,
        report_findings=kb.report_finding,
        findings=kb.finding,
        language="en",
    )
    assert [issue.code for issue in german.issues] == [
        issue.code for issue in english.issues
    ]
    assert german.issues[0].message == (
        "Vorlage 'Synthetische Vorlage' verweist auf den unbekannten Abschnitt "
        "'absent_section'."
    )
    assert english.issues[0].message.startswith("Template 'Synthetic template'")
