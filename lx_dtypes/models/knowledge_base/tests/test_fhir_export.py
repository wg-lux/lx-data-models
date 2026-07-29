from pathlib import Path
from typing import Any

import pytest

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
    infer_fhir_code_system_domain,
    import_fhir_terminology,
)
from lx_dtypes.models.knowledge_base.fhir_yaml import (
    fhir_to_yaml,
    knowledge_base_from_fhir,
    write_fhir_yaml,
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


def _sample_knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(
        config=KnowledgeBaseConfig(
            name="gastro_base",
            version="1.0.0",
            medical_field="gastroenterology",
        ),
        examination={
            "gastroscopy": Examination(
                name="gastroscopy",
                name_de="Gastroskopie",
                name_en="Gastroscopy",
                description="Upper GI endoscopy.",
                findings=["esophagitis"],
                kb_module_name="gastro_base",
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
            medical_field="gastroenterology",
        ),
    )

    bundle = kb.export_fhir_terminology(bundle=True)

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert {
        "url": f"{DEFAULT_FHIR_BASE_URL}/StructureDefinition/lx-medical-field",
        "valueCode": "gastroenterology",
    } in bundle["extension"]
    assert {
        "url": f"{DEFAULT_FHIR_BASE_URL}/StructureDefinition/lx-medical-field",
        "valueCode": "gastroenterology",
    } in bundle["entry"][0]["resource"]["extension"]
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
    assert imported["classification"][0]["classification_types"] == ["grading_system"]
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


def test_fhir_creates_validated_knowledge_base_with_stable_codes() -> None:
    source = _sample_knowledge_base()
    payload = source.export_fhir_terminology(bundle=True)

    imported = KnowledgeBase.from_fhir(
        payload,
        module_name="imported_gastro",
    )

    assert imported.config.name == "imported_gastro"
    assert imported.config.version == "1.0.0"
    assert imported.config.medical_field == "gastroenterology"
    assert "gastroscopy" in imported.examination
    assert imported.examination["gastroscopy"].name_en == "Gastroscopy"
    assert imported.examination["gastroscopy"].findings == ["esophagitis"]
    assert imported.finding["esophagitis"].classifications == ["la-classification"]
    assert imported.classification["la-classification"].classification_choices == [
        "la-grade-a",
        "la-grade-b",
    ]


def test_fhir_to_yaml_roundtrips_through_knowledge_base_loader(
    tmp_path: Path,
) -> None:
    payload = _sample_knowledge_base().export_fhir_terminology(bundle=True)

    yaml_text = fhir_to_yaml(payload, module_name="yaml_gastro")
    output_path = write_fhir_yaml(
        payload,
        tmp_path / "knowledge_base.yaml",
        module_name="yaml_gastro",
    )
    loaded = KnowledgeBase.create_from_yaml(output_path)

    assert output_path.read_text(encoding="utf-8") == yaml_text
    assert loaded.config.name == "yaml_gastro"
    assert loaded.examination["gastroscopy"].name_de == "Gastroskopie"
    assert loaded.finding["esophagitis"].classifications == ["la-classification"]


def test_high_level_fhir_import_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="no supported terminology"):
        knowledge_base_from_fhir({"resourceType": "Bundle", "entry": []})


def test_high_level_fhir_import_rejects_duplicate_codes() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "id": "lx-finding-cs",
        "concept": [
            {"code": "polyp", "display": "Polyp"},
            {"code": "polyp", "display": "Polyp duplicate"},
        ],
    }

    with pytest.raises(ValueError, match="Duplicate finding code 'polyp'"):
        knowledge_base_from_fhir(payload)


@pytest.mark.parametrize(
    ("code_system", "expected_domain"),
    [
        (
            {
                "resourceType": "CodeSystem",
                "id": "endoscopy-procedures",
                "title": "Diagnostic endoscopy procedures",
            },
            "examination",
        ),
        (
            {
                "resourceType": "CodeSystem",
                "id": "estado-civil",
                "title": "Estado Civil",
            },
            "classification_choice",
        ),
        (
            {
                "resourceType": "CodeSystem",
                "id": "measurement-units",
                "title": "Units of measure",
            },
            "unit",
        ),
        (
            {
                "resourceType": "CodeSystem",
                "id": "structural-evidence-wins",
                "title": "Finding status",
                "property": [{"code": "classification", "type": "Coding"}],
            },
            "finding",
        ),
        (
            {
                "resourceType": "CodeSystem",
                "id": "opaque-codes",
                "concept": [{"code": "x1", "display": "X1"}],
            },
            None,
        ),
    ],
)
def test_infer_fhir_code_system_domain_from_structure_and_metadata(
    code_system: dict[str, Any],
    expected_domain: str | None,
) -> None:
    assert infer_fhir_code_system_domain(code_system) == expected_domain


def test_structural_mapper_imports_generic_fhir_code_system() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "id": "clinical-findings",
        "title": "Clinical finding terminology",
        "concept": [
            {
                "code": "reflux",
                "display": "Gastroesophageal reflux",
                "definition": "Reflux finding.",
            }
        ],
    }

    imported = import_fhir_terminology(
        payload,
        module_name="generic_hapi",
        identifier_mode="code",
    )

    assert imported["finding"] == [
        {
            "name": "reflux",
            "name_de": "Gastroesophageal reflux",
            "name_en": "Gastroesophageal reflux",
            "description": "Reflux finding.",
            "tags": [],
            "kb_module_name": "generic_hapi",
            "finding_types": [],
            "classifications": [],
            "interventions": [],
            "caused_by_interventions": [],
        }
    ]


def test_structural_mapper_flattens_nested_fhir_concepts() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "id": "animal-taxonomy",
        "hierarchyMeaning": "is-a",
        "concept": [
            {
                "code": "animal",
                "display": "Animal",
                "concept": [
                    {"code": "dog", "display": "Dog"},
                    {
                        "code": "bird",
                        "display": "Bird",
                        "concept": [{"code": "canary", "display": "Canary"}],
                    },
                ],
            }
        ],
    }

    imported = import_fhir_terminology(payload, identifier_mode="code", language="en")

    assert [item["name"] for item in imported["classification_choice"]] == [
        "animal",
        "dog",
        "bird",
        "canary",
    ]


def test_structural_mapper_treats_complete_opaque_code_system_as_enumeration() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "url": "https://fhir.bfarm.de/CodeSystem/HealthAppManufacturerType",
        "content": "complete",
        "concept": [
            {"code": "legal", "display": "Juristische Person"},
            {"code": "natural", "display": "Natürliche Person"},
        ],
    }

    imported = import_fhir_terminology(payload, identifier_mode="code", language="de")

    assert [item["name"] for item in imported["classification_choice"]] == [
        "legal",
        "natural",
    ]
    assert imported["classification_choice"][0]["name_de"] == "Juristische Person"
    assert imported["classification_choice"][0]["name_en"] == "unknown"


def test_fhir_import_can_specify_display_language() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "id": "lx-finding-cs",
        "concept": [
            {
                "code": "refluxo",
                "display": "Refluxo gastroesofágico",
                "designation": [
                    {
                        "language": "en-US",
                        "value": "Gastroesophageal reflux",
                    }
                ],
            }
        ],
    }

    imported = import_fhir_terminology(
        payload,
        identifier_mode="code",
        language="pt-BR",
    )

    assert imported["finding"][0]["name"] == "refluxo"
    assert imported["finding"][0]["name_en"] == "Gastroesophageal reflux"
    assert imported["finding"][0]["name_de"] == "unknown"


def test_fhir_import_uses_display_for_selected_lxdm_language() -> None:
    payload = {
        "resourceType": "CodeSystem",
        "id": "lx-finding-cs",
        "concept": [{"code": "reflux", "display": "Refluxkrankheit"}],
    }

    imported = KnowledgeBase.import_fhir_terminology(payload, language="de-DE")

    assert imported["finding"][0]["name_de"] == "Refluxkrankheit"
    assert imported["finding"][0]["name_en"] == "unknown"


def test_fhir_import_supports_per_code_system_languages() -> None:
    payload = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "CodeSystem",
                    "id": "lx-finding-cs",
                    "language": "de",
                    "concept": [{"code": "reflux", "display": "Refluxkrankheit"}],
                }
            },
            {
                "resource": {
                    "resourceType": "CodeSystem",
                    "id": "lx-examination-cs",
                    "language": "en-GB",
                    "concept": [{"code": "egd", "display": "Gastroscopy"}],
                }
            },
        ],
    }

    imported = import_fhir_terminology(payload, identifier_mode="code")

    assert imported["finding"][0]["name_de"] == "Refluxkrankheit"
    assert imported["finding"][0]["name_en"] == "unknown"
    assert imported["examination"][0]["name_en"] == "Gastroscopy"
    assert imported["examination"][0]["name_de"] == "unknown"


def test_fhir_import_rejects_invalid_language_tag() -> None:
    with pytest.raises(ValueError, match="IETF language tag"):
        import_fhir_terminology(
            {"resourceType": "CodeSystem", "id": "lx-finding-cs"},
            language="not a language",
        )
