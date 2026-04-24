from typing import Any

from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base.classification.Classification import (
    Classification,
)
from lx_dtypes.models.knowledge_base.classification.ClassificationType import (
    ClassificationType,
)
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.fhir import (
    DEFAULT_FHIR_BASE_URL,
    import_fhir_terminology,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit


def _resource_by_id(
    resources: list[dict[str, Any]], resource_id: str
) -> dict[str, Any]:
    return next(resource for resource in resources if resource["id"] == resource_id)


def _concept_by_code(code_system: dict[str, Any], code: str) -> dict[str, Any]:
    return next(
        concept for concept in code_system["concept"] if concept["code"] == code
    )


def test_knowledge_base_exports_fhir_terminology_resources() -> None:
    kb = KnowledgeBase(
        config=KnowledgeBaseConfig(
            name="gastro_base",
            version="1.0.0",
        ),
        examination={
            "gastroscopy": Examination(
                name="gastroscopy",
                name_de="Gastroskopie",
                name_en="Gastroscopy",
                description="Upper GI endoscopy.",
                findings=["esophagitis"],
                kb_module_name="gastro_base",
                tags=["endoscopy"],
                uuid="2cfa2d8f-7a1b-4f74-9b67-1a0f7c29a111",
            )
        },
        finding={
            "esophagitis": Finding(
                name="esophagitis",
                description="Inflammation of the esophageal mucosa.",
                classifications=["la_classification"],
                kb_module_name="gastro_base",
            )
        },
        classification_type={
            "grading_system": ClassificationType(
                name="grading_system",
                description="Severity grading system.",
                kb_module_name="gastro_base",
            )
        },
        classification={
            "la_classification": Classification(
                name="la_classification",
                description="Los Angeles classification.",
                classification_types=["grading_system"],
                classification_choices=["la_grade_a", "la_grade_b"],
                kb_module_name="gastro_base",
            )
        },
        classification_choice={
            "la_grade_a": ClassificationChoice(
                name="la_grade_a",
                description="Grade A.",
                kb_module_name="gastro_base",
            ),
            "la_grade_b": ClassificationChoice(
                name="la_grade_b",
                description="Grade B.",
                kb_module_name="gastro_base",
            ),
        },
        unit={
            "mm": Unit(
                name="mm",
                description="Millimeter.",
                abbreviation="mm",
                kb_module_name="gastro_base",
            )
        },
    )

    exported = kb.export_fhir_terminology()

    code_systems = exported["code_systems"]
    value_sets = exported["value_sets"]
    assert len(code_systems) == 6

    examination_cs = _resource_by_id(code_systems, "lx-examination-cs")
    gastroscopy = _concept_by_code(examination_cs, "gastroscopy")
    assert gastroscopy["designation"] == [
        {"language": "de", "value": "Gastroskopie"},
        {"language": "en", "value": "Gastroscopy"},
    ]
    assert {
        "code": "finding",
        "valueCoding": {
            "system": f"{DEFAULT_FHIR_BASE_URL}/CodeSystem/lx-finding-cs",
            "code": "esophagitis",
            "display": "esophagitis",
        },
    } in gastroscopy["property"]

    classification_cs = _resource_by_id(code_systems, "lx-classification-cs")
    la_classification = _concept_by_code(classification_cs, "la-classification")
    assert {
        "code": "classification-type",
        "valueCoding": {
            "system": f"{DEFAULT_FHIR_BASE_URL}/CodeSystem/lx-classification-type-cs",
            "code": "grading-system",
            "display": "grading_system",
        },
    } in la_classification["property"]

    choice_cs = _resource_by_id(code_systems, "lx-classification-choice-cs")
    la_grade_a = _concept_by_code(choice_cs, "la-grade-a")
    assert {
        "code": "classification",
        "valueCoding": {
            "system": f"{DEFAULT_FHIR_BASE_URL}/CodeSystem/lx-classification-cs",
            "code": "la-classification",
            "display": "la_classification",
        },
    } in la_grade_a["property"]

    choice_vs = _resource_by_id(
        value_sets,
        "lx-classification-choice-for-la-classification-vs",
    )
    assert choice_vs["compose"]["include"][0]["concept"] == [
        {"code": "la-grade-a", "display": "la_grade_a"},
        {"code": "la-grade-b", "display": "la_grade_b"},
    ]


def test_knowledge_base_exports_fhir_terminology_bundle() -> None:
    kb = KnowledgeBase(
        config=KnowledgeBaseConfig(
            name="empty",
            version="1.0.0",
        ),
    )

    bundle = kb.export_fhir_terminology(bundle=True)

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert len(bundle["entry"]) == 12


def test_fhir_terminology_import_roundtrips_exported_concepts() -> None:
    kb = KnowledgeBase(
        config=KnowledgeBaseConfig(
            name="gastro_base",
            version="1.0.0",
        ),
        examination={
            "gastroscopy": Examination(
                name="gastroscopy",
                name_de="Gastroskopie",
                name_en="Gastroscopy",
                description="Upper GI endoscopy.",
                findings=["esophagitis"],
                kb_module_name="gastro_base",
                tags=["endoscopy"],
                uuid="2cfa2d8f-7a1b-4f74-9b67-1a0f7c29a111",
            )
        },
        finding={
            "esophagitis": Finding(
                name="esophagitis",
                description="Inflammation of the esophageal mucosa.",
                classifications=["la_classification"],
                kb_module_name="gastro_base",
            )
        },
        classification_type={
            "grading_system": ClassificationType(
                name="grading_system",
                description="Severity grading system.",
                kb_module_name="gastro_base",
            )
        },
        classification={
            "la_classification": Classification(
                name="la_classification",
                description="Los Angeles classification.",
                classification_types=["grading_system"],
                classification_choices=["la_grade_a", "la_grade_b"],
                kb_module_name="gastro_base",
            )
        },
        classification_choice={
            "la_grade_a": ClassificationChoice(
                name="la_grade_a",
                description="Grade A.",
                kb_module_name="gastro_base",
            ),
            "la_grade_b": ClassificationChoice(
                name="la_grade_b",
                description="Grade B.",
                kb_module_name="gastro_base",
            ),
        },
        unit={
            "mm": Unit(
                name="mm",
                description="Millimeter.",
                abbreviation="mm",
                kb_module_name="gastro_base",
            )
        },
    )

    imported = import_fhir_terminology(
        kb.export_fhir_terminology(),
        module_name="fallback_module",
    )

    assert imported["examination"][0]["findings"] == ["esophagitis"]
    assert imported["finding"][0]["classifications"] == ["la_classification"]
    assert imported["classification"][0]["classification_types"] == [
        "grading_system"
    ]
    assert imported["classification"][0]["classification_choices"] == [
        "la_grade_a",
        "la_grade_b",
    ]
    assert imported["classification_choice"][0]["name"] == "la_grade_a"
    assert imported["unit"][0]["abbreviation"] == "mm"
    assert imported["examination"][0]["uuid"] == (
        "2cfa2d8f-7a1b-4f74-9b67-1a0f7c29a111"
    )
    assert imported["examination"][0]["tags"] == ["endoscopy"]


def test_knowledge_base_import_fhir_terminology_convenience_method() -> None:
    code_system = {
        "resourceType": "CodeSystem",
        "id": "lx-finding-cs",
        "url": f"{DEFAULT_FHIR_BASE_URL}/CodeSystem/lx-finding-cs",
        "concept": [
            {
                "code": "esophagitis",
                "display": "esophagitis",
                "definition": "Inflammation.",
            }
        ],
    }

    imported = KnowledgeBase.import_fhir_terminology(
        code_system,
        module_name="gastro_base",
    )

    assert imported["finding"] == [
        {
            "name": "esophagitis",
            "name_de": "esophagitis",
            "name_en": "esophagitis",
            "description": "Inflammation.",
            "tags": [],
            "kb_module_name": "gastro_base",
            "finding_types": [],
            "classifications": [],
            "interventions": [],
            "caused_by_interventions": [],
        }
    ]
