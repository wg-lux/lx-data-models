"""Registries are the single source of truth; typed copies must agree with them.

Typing requires some names to be declared again (Pydantic fields, TypedDict
keys). These tests fail when such a copy drifts from the registry, and check
that export and reload round trips are idempotent.
"""

from __future__ import annotations

from pathlib import Path
from typing import get_args, get_type_hints

import pytest

from lx_dtypes.models.contracts.package_snapshot import (
    PackageSnapshot,
    build_package_snapshot,
    restore_package_snapshot,
)
from lx_dtypes.models.interface.data_formats import read_record, write_record
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import (
    KnowledgeBase,
    KnowledgeBaseDDict,
    KnowledgeBaseRecordList,
)
from lx_dtypes.models.interface.Ledger import (
    EXAMINATION_RECORD_LIST_KEYS,
    FLAT_LEDGER_COLLECTIONS,
    Ledger,
    LedgerDataDict,
    LedgerRecordList,
)
from lx_dtypes.models.knowledge_base.pydantic_main import (
    KB_MODEL_NAMES_LITERAL,
    KB_MODEL_NAMES_ORDERED,
    knowledge_base_models_lookup,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Pydantic import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.models.ledger.p_indication.Pydantic import PIndication
from lx_dtypes.models.ledger.p_indication_classification.Pydantic import (
    PIndicationClassification,
)
from lx_dtypes.models.ledger.p_intervention.Pydantic import PFindingIntervention
from lx_dtypes.models.ledger.p_interventions.Pydantic import PFindingInterventions
from lx_dtypes.models.ledger.pydantic_main import (
    L_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_ORDERED,
    ledger_models_lookup,
)
from lx_dtypes.utils.parser import camel_to_snake
from tests.paths import PACKAGE_ROOT

KB_FIELDS = [camel_to_snake(name) for name in KB_MODEL_NAMES_ORDERED]
# Ledger collections exported elsewhere: cases by the standardized CSV export,
# examinations as trees through ``EXAMINATION_RECORD_LIST_KEYS``.
LEDGER_FIELDS_NOT_FLAT = {"cases", "patient_examinations"}


def test_name_lists_are_derived_from_one_literal() -> None:
    assert KB_MODEL_NAMES_ORDERED == list(get_args(KB_MODEL_NAMES_LITERAL))
    assert L_MODEL_NAMES_ORDERED == list(get_args(L_MODEL_NAMES_LITERAL))
    assert len(set(KB_MODEL_NAMES_ORDERED)) == len(KB_MODEL_NAMES_ORDERED)
    assert len(set(L_MODEL_NAMES_ORDERED)) == len(L_MODEL_NAMES_ORDERED)
    assert set(KB_MODEL_NAMES_ORDERED) <= set(knowledge_base_models_lookup)
    assert set(L_MODEL_NAMES_ORDERED) <= set(ledger_models_lookup)


def test_knowledge_base_declarations_match_the_registry() -> None:
    collections = {
        name
        for name, field in KnowledgeBase.model_fields.items()
        if name != "report_template_lifecycle_status"
        and getattr(field.annotation, "__origin__", None) is dict
    }
    assert collections == set(KB_FIELDS)
    assert set(KB_FIELDS) <= set(get_type_hints(KnowledgeBaseDDict))
    assert set(get_type_hints(KnowledgeBaseRecordList)) == {
        f"{field}s" for field in KB_FIELDS
    }


def test_ledger_declarations_match_the_export_tables() -> None:
    collections = {
        name
        for name, field in Ledger.model_fields.items()
        if getattr(field.annotation, "__origin__", None) is dict
    }
    assert set(FLAT_LEDGER_COLLECTIONS.values()) == collections - LEDGER_FIELDS_NOT_FLAT
    assert set(get_type_hints(LedgerRecordList)) == (
        set(FLAT_LEDGER_COLLECTIONS) | set(EXAMINATION_RECORD_LIST_KEYS)
    )
    assert collections <= set(get_type_hints(LedgerDataDict))


def _examination(number: int) -> PExamination:
    exam = PExamination(examination="colonoscopy", patient=f"patient-{number}")
    for index in range(2):
        indication = PIndication(
            indication=f"indication-{number}-{index}",
            patient_examination=str(exam.uuid),
        )
        indication.patient_indication_classifications.append(
            PIndicationClassification(
                classification="c",
                classification_choice=f"ic-{number}-{index}",
                patient_indication=str(indication.uuid),
            )
        )
        exam.patient_indications.append(indication)

        finding = PFinding(
            finding=f"finding-{number}-{index}", patient_examination=str(exam.uuid)
        )
        group = PFindingClassifications(patient_finding=str(finding.uuid))
        choice = PFindingClassificationChoice(
            classification="c",
            classification_choice=f"choice-{number}-{index}",
            patient_finding_classifications=str(group.uuid),
        )
        choice.patient_finding_classification_choice_descriptors.append(
            PFindingClassificationChoiceDescriptor(
                classification_choice_descriptor="d",
                descriptor_value=float(number * 10 + index),
                patient_finding_classification_choice=str(choice.uuid),
            )
        )
        group.patient_finding_classification_choices.append(choice)
        finding.patient_finding_classifications.append(group)
        interventions = PFindingInterventions(patient_finding=str(finding.uuid))
        interventions.patient_finding_interventions.append(
            PFindingIntervention(
                intervention=f"intervention-{number}-{index}",
                patient_finding_interventions=str(interventions.uuid),
            )
        )
        finding.patient_finding_interventions.append(interventions)
        exam.patient_findings.append(finding)
    return exam


@pytest.fixture
def ledger() -> Ledger:
    exams = [_examination(1), _examination(2)]
    return Ledger(patient_examinations={str(exam.uuid): exam for exam in exams})


def test_examination_trees_flatten_in_nesting_order(ledger: Ledger) -> None:
    records = ledger.export_record_lists()

    assert [f["finding"] for f in records["p_findings"]] == [
        "finding-1-0",
        "finding-1-1",
        "finding-2-0",
        "finding-2-1",
    ]
    assert [
        c["classification_choice"] for c in records["p_finding_classification_choices"]
    ] == [
        "choice-1-0",
        "choice-1-1",
        "choice-2-0",
        "choice-2-1",
    ]
    assert [
        d["descriptor_value"]
        for d in records["p_finding_classification_choice_descriptors"]
    ] == [10.0, 11.0, 20.0, 21.0]
    assert [i["intervention"] for i in records["p_finding_intervention"]] == [
        "intervention-1-0",
        "intervention-1-1",
        "intervention-2-0",
        "intervention-2-1",
    ]
    assert [
        c["classification_choice"] for c in records["p_indication_classifications"]
    ] == ["ic-1-0", "ic-1-1", "ic-2-0", "ic-2-1"]
    assert records["patients"] == [] and records.get("p_time_offsets") == []


def test_ledger_export_and_reload_are_idempotent(
    ledger: Ledger, tmp_path: Path
) -> None:
    first = ledger.export_record_lists()
    assert ledger.export_record_lists() == first

    path = tmp_path / "ledger.yml"
    write_record(Ledger, ledger, path)
    reloaded = read_record(Ledger, path)
    assert reloaded.export_record_lists() == first
    write_record(Ledger, reloaded, tmp_path / "again.yml")
    assert (tmp_path / "again.yml").read_bytes() == path.read_bytes()


def test_knowledge_base_snapshot_round_trip_is_a_fixed_point() -> None:
    loader = DataLoader(input_dirs=[PACKAGE_ROOT / "data"])
    loader.load_module_configs()
    kb = loader.load_knowledge_base("report_template_examples")

    snapshot = build_package_snapshot(kb)
    restored = restore_package_snapshot(
        PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    )
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id
