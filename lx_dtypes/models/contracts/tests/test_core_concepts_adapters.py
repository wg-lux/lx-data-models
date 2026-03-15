from __future__ import annotations

from typing import Any, Callable
from pathlib import Path

import pytest

from lx_dtypes.models.contracts import (
    core_concept_to_storage,
    kb_to_core_concepts_payload,
    record_to_core_concept,
)
from lx_dtypes.models.contracts.adapters import CoreConceptName
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.classification.Classification import Classification
from lx_dtypes.models.knowledge_base.classification_choice.ClassificationChoice import (
    ClassificationChoice,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.examination.Examination import Examination
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.finding._FindingType import FindingType
from lx_dtypes.models.knowledge_base.indication.Indication import Indication
from lx_dtypes.models.knowledge_base.indication.IndicationType import IndicationType
from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
    InformationSource,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
    InformationSourceType,
)
from lx_dtypes.models.knowledge_base.intervention.Intervention import Intervention
from lx_dtypes.models.knowledge_base.intervention.InterventionType import (
    InterventionType,
)
from lx_dtypes.models.knowledge_base.unit.Unit import Unit
from lx_dtypes.models.knowledge_base.unit.UnitType import UnitType

_LIST_FIELDS: dict[CoreConceptName, list[str]] = {
    "classification": ["classification_choices", "classification_types"],
    "classification_choice": ["classification_choice_descriptors"],
    "classification_choice_descriptor": ["selection_options"],
    "examination": ["findings", "examination_types", "indications"],
    "finding": ["finding_types", "classifications", "interventions"],
    "finding_type": [],
    "indication": ["indication_types", "interventions"],
    "indication_type": [],
    "intervention": ["intervention_types"],
    "intervention_type": [],
    "unit": ["unit_types"],
    "unit_type": [],
    "information_source": ["information_source_types"],
    "information_source_type": [],
    "citation": ["authors", "keywords"],
}


def _sample_storage_by_concept() -> dict[CoreConceptName, dict[str, Any]]:
    return {
        "classification": {
            "name": "classification_a",
            "classification_choices": "choice_1,choice_2",
            "classification_types": "type_1",
            "tags": "tag_a,tag_b",
        },
        "classification_choice": {
            "name": "choice_a",
            "classification_choice_descriptors": "descriptor_1,descriptor_2",
            "tags": "tag_a,tag_b",
        },
        "classification_choice_descriptor": {
            "name": "descriptor_a",
            "classification_choice_descriptor_type": "numeric",
            "unit": "mm",
            "numeric_distribution": "uniform",
            "selection_options": "opt_1,opt_2",
            "tags": "tag_a,tag_b",
        },
        "examination": {
            "name": "exam_a",
            "findings": "finding_1,finding_2",
            "examination_types": "exam_type_1",
            "indications": "indication_1",
            "tags": "tag_a,tag_b",
        },
        "finding": {
            "name": "finding_a",
            "finding_types": "finding_type_1",
            "classifications": "classification_1,classification_2",
            "interventions": "intervention_1",
            "tags": "tag_a,tag_b",
        },
        "finding_type": {
            "name": "finding_type_a",
            "tags": "tag_a,tag_b",
        },
        "indication": {
            "name": "indication_a",
            "indication_types": "indication_type_1",
            "interventions": "intervention_1,intervention_2",
            "tags": "tag_a,tag_b",
        },
        "indication_type": {
            "name": "indication_type_a",
            "tags": "tag_a,tag_b",
        },
        "intervention": {
            "name": "intervention_a",
            "intervention_types": "intervention_type_1",
            "tags": "tag_a,tag_b",
        },
        "intervention_type": {
            "name": "intervention_type_a",
            "tags": "tag_a,tag_b",
        },
        "unit": {
            "name": "unit_a",
            "abbreviation": "mm",
            "unit_types": "unit_type_1",
            "tags": "tag_a,tag_b",
        },
        "unit_type": {
            "name": "unit_type_a",
            "tags": "tag_a,tag_b",
        },
        "information_source": {
            "name": "source_a",
            "information_source_types": "source_type_1",
            "tags": "tag_a,tag_b",
        },
        "information_source_type": {
            "name": "source_type_a",
            "tags": "tag_a,tag_b",
        },
        "citation": {
            "name": "citation_a",
            "citation_key": "citation_key_a",
            "title": "Citation title",
            "authors": "author_a,author_b",
            "keywords": "kw_a,kw_b",
            "identifiers": {"pmid": "123"},
            "tags": "tag_a,tag_b",
        },
    }


def _sample_model_factories() -> dict[CoreConceptName, Callable[[], Any]]:
    return {
        "classification": lambda: Classification(
            name="classification_model",
            classification_choices=["choice_1", "choice_2"],
            classification_types=["type_1"],
            tags=["tag_a", "tag_b"],
        ),
        "classification_choice": lambda: ClassificationChoice(
            name="choice_model",
            classification_choice_descriptors=["descriptor_1", "descriptor_2"],
            tags=["tag_a", "tag_b"],
        ),
        "classification_choice_descriptor": lambda: ClassificationChoiceDescriptor(
            name="descriptor_model",
            classification_choice_descriptor_type="numeric",
            unit="mm",
            numeric_distribution="uniform",
            selection_options=["opt_1", "opt_2"],
            tags=["tag_a", "tag_b"],
        ),
        "examination": lambda: Examination(
            name="exam_model",
            findings=["finding_1", "finding_2"],
            examination_types=["exam_type_1"],
            indications=["indication_1"],
            tags=["tag_a", "tag_b"],
        ),
        "finding": lambda: Finding(
            name="finding_model",
            finding_types=["finding_type_1"],
            classifications=["classification_1", "classification_2"],
            interventions=["intervention_1"],
            tags=["tag_a", "tag_b"],
        ),
        "finding_type": lambda: FindingType(
            name="finding_type_model",
            tags=["tag_a", "tag_b"],
        ),
        "indication": lambda: Indication(
            name="indication_model",
            indication_types=["indication_type_1"],
            interventions=["intervention_1", "intervention_2"],
            tags=["tag_a", "tag_b"],
        ),
        "indication_type": lambda: IndicationType(
            name="indication_type_model",
            tags=["tag_a", "tag_b"],
        ),
        "intervention": lambda: Intervention(
            name="intervention_model",
            intervention_types=["intervention_type_1"],
            tags=["tag_a", "tag_b"],
        ),
        "intervention_type": lambda: InterventionType(
            name="intervention_type_model",
            tags=["tag_a", "tag_b"],
        ),
        "unit": lambda: Unit(
            name="unit_model",
            abbreviation="mm",
            unit_types=["unit_type_1"],
            tags=["tag_a", "tag_b"],
        ),
        "unit_type": lambda: UnitType(
            name="unit_type_model",
            tags=["tag_a", "tag_b"],
        ),
        "information_source": lambda: InformationSource(
            name="source_model",
            information_source_types=["source_type_1"],
            tags=["tag_a", "tag_b"],
        ),
        "information_source_type": lambda: InformationSourceType(
            name="source_type_model",
            tags=["tag_a", "tag_b"],
        ),
        "citation": lambda: Citation(
            name="citation_model",
            citation_key="citation_key_model",
            title="Citation title",
            authors=["author_a", "author_b"],
            keywords=["kw_a", "kw_b"],
            identifiers={"pmid": "123"},
            tags=["tag_a", "tag_b"],
        ),
    }


@pytest.mark.parametrize("concept", list(_LIST_FIELDS.keys()))
def test_core_concept_roundtrip_storage_conversion(concept: CoreConceptName) -> None:
    sample = _sample_storage_by_concept()[concept]

    canonical = record_to_core_concept(concept, sample)
    storage = core_concept_to_storage(concept, canonical)
    canonical_roundtrip = record_to_core_concept(concept, storage)

    for field in _LIST_FIELDS[concept]:
        assert isinstance(storage[field], str)
        assert isinstance(getattr(canonical, field), list)

    assert canonical_roundtrip.model_dump(mode="python") == canonical.model_dump(
        mode="python"
    )


@pytest.mark.parametrize("concept", list(_LIST_FIELDS.keys()))
def test_core_concept_model_and_ddict_parity(concept: CoreConceptName) -> None:
    factory = _sample_model_factories()[concept]
    model_instance = factory()

    canonical_from_model = record_to_core_concept(concept, model_instance)
    canonical_from_ddict = record_to_core_concept(concept, model_instance.ddict)

    assert canonical_from_model.model_dump(
        mode="python"
    ) == canonical_from_ddict.model_dump(mode="python")


def test_kb_to_core_concepts_payload_exports_all_concepts() -> None:
    package_data_dir = Path(__file__).resolve().parents[3] / "data"
    loader = DataLoader(input_dirs=[package_data_dir])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    payload = kb_to_core_concepts_payload(kb)
    dumped = payload.model_dump(mode="python")

    assert dumped["module_name"] == "report_template_examples"
    for concept in _LIST_FIELDS:
        assert concept in dumped
        assert isinstance(dumped[concept], list)
