import pytest
import yaml
from pydantic import ValidationError

from lx_dtypes.models.contracts.table_import import TableImportVocabulary
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base
from lx_dtypes.models.interface.table_import import load_table_import_vocabulary


def test_suggestions_preserve_ambiguity_and_do_not_guess_identity():
    vocabulary = load_table_import_vocabulary()
    assert vocabulary.suggest_columns(
        [
            " Vorname ",
            "FIRST NAME",
            "Nachname",
            "Geburtsdatum",
            "patient_id",
            "id",
            "name",
            "date",
            "Befund",
        ]
    ) == {
        "first_name": [" Vorname ", "FIRST NAME"],
        "last_name": ["Nachname"],
        "dob": ["Geburtsdatum"],
    }
    assert vocabulary.fields["gender"].values["weiblich"] == "female"
    assert "0" not in vocabulary.fields["gender"].values
    vocabulary.fields["gender"].values.clear()
    assert load_table_import_vocabulary().fields["gender"].values


def test_value_targets_exist_in_packaged_definitions():
    root = package_data_root() / "terminology"
    vocabulary = load_table_import_vocabulary()
    reference = load_knowledge_base(
        "endoreg_reference", input_dirs=[package_data_root()]
    )
    genders = {
        record.name for record in reference.reference_catalog["gender"].payload.records
    }
    examinations: set[str] = set()
    for path in (root / "lx_examinations/data").glob("*.yaml"):
        examinations.update(
            record["name"]
            for record in yaml.safe_load(path.read_text())
            if record["model"] == "examination"
        )
    assert set(vocabulary.fields["gender"].values.values()) <= genders
    assert set(vocabulary.fields["examination"].values.values()) <= examinations


@pytest.mark.parametrize(
    "fields",
    [
        {"unknown": {"aliases": ["something"]}},
        {"dob": {"aliases": ["DOB", " dob "]}},
        {"dob": {"aliases": [" "]}},
        {"dob": {"aliases": ["date"]}, "examination_date": {"aliases": ["DATE"]}},
        {"gender": {"aliases": ["gender"], "values": {"": "female"}}},
    ],
)
def test_invalid_vocabulary_is_rejected(fields: object):
    with pytest.raises(ValidationError):
        TableImportVocabulary.model_validate(
            {"schema_version": "1.0", "fields": fields}
        )


def test_selected_kb_concepts_cover_all_configured_collections():
    from lx_dtypes import load_knowledge_base
    from lx_dtypes.utils.parser import camel_to_snake

    kb = load_knowledge_base("DGVS_Terminology", input_dirs=[package_data_root()])
    vocabulary = load_table_import_vocabulary(kb)
    expected = {
        (kind, name)
        for kind in vocabulary.concept_models
        for name in getattr(kb, camel_to_snake(kind))
    }
    assert {(c.concept_type, c.name) for c in vocabulary.concepts} == expected
    assert len(vocabulary.concepts) > 500
    for concept in vocabulary.concepts:
        assert concept in vocabulary.suggest_concepts(
            concept.name, concept_type=concept.concept_type
        )
        assert concept.knowledge_base == kb.config.knowledge_base_identity
    assert {c.name for c in vocabulary.suggest_concepts("  kOlO ")} == {"colonoscopy"}
    assert {
        c.name
        for c in vocabulary.suggest_concepts(
            "Lokalisation", concept_type="Classification"
        )
    } >= {"colonoscopy_location_default", "colonoscopy_location_coarse"}
    assert all(c.name == "unknown" for c in vocabulary.suggest_concepts("unknown"))
    assert vocabulary.suggest_concepts("not a clinical term") == []


def test_custom_labels_ambiguity_and_absent_targets():
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
    from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
    from lx_dtypes.models.knowledge_base.finding import Finding

    kb = KnowledgeBase(
        config=KnowledgeBaseConfig(name="synthetic", version="1.0.0"),
        finding={
            name: Finding(
                name=name,
                name_en="Shared label",
                name_de="Gemeinsamer Befund",
                kb_module_name="synthetic",
            )
            for name in ("first", "second")
        },
    )
    vocabulary = load_table_import_vocabulary(kb)
    assert [c.name for c in vocabulary.suggest_concepts("SHARED LABEL")] == [
        "first",
        "second",
    ]
    assert len(vocabulary.suggest_concepts("Gemeinsamer Befund")) == 2
    assert vocabulary.suggest_concepts("Shared label", concept_type="Examination") == []
    assert vocabulary.suggest_concepts("Koloskopie") == []
    assert load_table_import_vocabulary().concepts == []


@pytest.mark.parametrize(
    "extra",
    [
        {"concept_models": ["InventedConcept"]},
        {"concept_models": ["Finding", "Finding"]},
        {"concept_aliases": {"Finding": {"lesion": ["lesion"]}}},
        {
            "concept_models": ["Finding"],
            "concept_aliases": {"Finding": {"lesion": [" "]}},
        },
    ],
)
def test_invalid_concept_configuration_is_rejected(extra: dict[str, object]):
    with pytest.raises(ValidationError):
        TableImportVocabulary.model_validate(
            {
                "schema_version": "1.0",
                "fields": {"dob": {"aliases": ["dob"]}},
                **extra,
            }
        )
