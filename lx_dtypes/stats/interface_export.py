from typing import List

# import numpy as np
import pandas as pd

from lx_dtypes.models.core.center_shallow import CenterShallowDataDict
from lx_dtypes.models.ledger.examiner import ExaminerShallowDataDict
from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase
from lx_dtypes.models.ledger.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorShallowDataDict,
)

# from lx_dtypes.models.patient.patient import PatientDataDictShallow
from lx_dtypes.models.ledger.patient_examination import (
    PatientExaminationShallowDataDict,
)
from lx_dtypes.models.ledger.patient_finding import PatientFindingShallowDataDict
from lx_dtypes.models.ledger.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceShallowDataDict,
)
from lx_dtypes.models.ledger.patient_finding_classifications import (
    PatientFindingClassificationsShallowDataDict,
)
from lx_dtypes.models.ledger.patient_ledger import PatientLedger
from lx_dtypes.models.patient_interface import PatientInterface

from .dataset import InterfaceExportDataset, KnowledgeBaseDataset, PatientLedgerDataset
from .schemas import (
    CenterShallowSchema,
    # Knowledge Base
    CitationShallowSchema,
    ClassificationChoiceDescriptorShallowSchema,
    ClassificationChoiceShallowSchema,
    ClassificationShallowSchema,
    ClassificationTypeShallowSchema,
    ExaminationShallowSchema,
    ExaminationTypeShallowSchema,
    ExaminerShallowSchema,
    FindingShallowSchema,
    FindingTypeShallowSchema,
    IndicationShallowSchema,
    IndicationTypeShallowSchema,
    InformationSourceShallowSchema,
    InterventionShallowSchema,
    InterventionTypeShallowSchema,
    PatientExaminationShallowSchema,
    PatientFindingClassificationChoiceDescriptorShallowSchema,
    PatientFindingClassificationChoiceShallowSchema,
    PatientFindingClassificationsShallowSchema,
    PatientFindingShallowSchema,
    PatientShallowSchema,
    UnitShallowSchema,
    UnitTypeShallowSchema,
)


def ledger2dataset(
    ledger: PatientLedger,
) -> PatientLedgerDataset:
    patient_dicts = [p.to_ddict_shallow() for _, p in ledger.patients.items()]
    examination_dicts: List[PatientExaminationShallowDataDict] = []
    finding_dicts: List[PatientFindingShallowDataDict] = []
    classifications_dicts: List[PatientFindingClassificationsShallowDataDict] = []
    choices_dicts: List[PatientFindingClassificationChoiceShallowDataDict] = []
    descriptors_dicts: List[
        PatientFindingClassificationChoiceDescriptorShallowDataDict
    ] = []
    center_dicts: List[CenterShallowDataDict] = []
    examiner_dicts: List[ExaminerShallowDataDict] = []

    # Serialize Examinations, Findings, Classifications, Choices, Descriptors
    examinations = [e for _, e in ledger.examinations.items()]
    for exam in examinations:
        examination_dicts.append(exam.to_ddict_shallow())
        for finding in exam.findings:
            finding_dicts.append(finding.to_ddict_shallow())
            if finding.classifications:
                classifications_dicts.append(finding.classifications.to_ddict_shallow())
                for choice in finding.classifications.choices:
                    choices_dicts.append(choice.to_ddict_shallow())
                    for descriptor in choice.descriptors:
                        descriptors_dicts.append(descriptor.to_ddict_shallow())

    # Serialize Centers and Examiners
    centers = [c for _, c in ledger.centers.items()]

    for center in centers:
        center_dicts.append(center.to_ddict_shallow())
        center_examiners = center.examiners
        for _, examiner in center_examiners.items():
            examiner_dicts.append(examiner.to_ddict_shallow())

    # Construct DataFrames
    df_patients = PatientShallowSchema.validate(pd.DataFrame(patient_dicts))
    df_examinations = PatientExaminationShallowSchema.validate(
        pd.DataFrame(examination_dicts)
    )
    df_findings = PatientFindingShallowSchema.validate(pd.DataFrame(finding_dicts))
    df_classifications = PatientFindingClassificationsShallowSchema.validate(
        pd.DataFrame(classifications_dicts)
    )
    df_choices = PatientFindingClassificationChoiceShallowSchema.validate(
        pd.DataFrame(choices_dicts)
    )
    df_descriptors = PatientFindingClassificationChoiceDescriptorShallowSchema.validate(
        pd.DataFrame(descriptors_dicts)
    )
    df_centers = CenterShallowSchema.validate(pd.DataFrame(center_dicts))
    df_examiners = ExaminerShallowSchema.validate(pd.DataFrame(examiner_dicts))

    dataset = PatientLedgerDataset(
        patients=df_patients,
        examinations=df_examinations,
        findings=df_findings,
        classifications=df_classifications,
        classification_choices=df_choices,
        classification_choice_descriptors=df_descriptors,
        centers=df_centers,
        examiners=df_examiners,
    )

    return dataset


def kb2dataset(kb: KnowledgeBase) -> KnowledgeBaseDataset:
    record_lists_dict = kb.export_record_lists()
    citations = CitationShallowSchema.validate(
        pd.DataFrame(record_lists_dict["citations"])
    )
    classification_types = ClassificationTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["classification_types"])
    )
    classifications = ClassificationShallowSchema.validate(
        pd.DataFrame(record_lists_dict["classifications"])
    )
    classification_choices = ClassificationChoiceShallowSchema.validate(
        pd.DataFrame(record_lists_dict["classification_choices"])
    )
    classification_choice_descriptors = (
        ClassificationChoiceDescriptorShallowSchema.validate(
            pd.DataFrame(record_lists_dict["classification_choice_descriptors"])
        )
    )
    examination_types = ExaminationTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["examination_types"])
    )
    examinations = ExaminationShallowSchema.validate(
        pd.DataFrame(record_lists_dict["examinations"])
    )
    finding_types = FindingTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["finding_types"])
    )
    findings = FindingShallowSchema.validate(
        pd.DataFrame(record_lists_dict["findings"])
    )
    indication_types = IndicationTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["indication_types"])
    )
    indications = IndicationShallowSchema.validate(
        pd.DataFrame(record_lists_dict["indications"])
    )
    information_sources = InformationSourceShallowSchema.validate(
        pd.DataFrame(record_lists_dict["information_sources"])
    )
    intervention_types = InterventionTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["intervention_types"])
    )
    interventions = InterventionShallowSchema.validate(
        pd.DataFrame(record_lists_dict["interventions"])
    )
    unit_types = UnitTypeShallowSchema.validate(
        pd.DataFrame(record_lists_dict["unit_types"])
    )
    units = UnitShallowSchema.validate(pd.DataFrame(record_lists_dict["units"]))
    dataset = KnowledgeBaseDataset(
        citations=citations,
        classification_types=classification_types,
        classifications=classifications,
        classification_choices=classification_choices,
        classification_choice_descriptors=classification_choice_descriptors,
        examination_types=examination_types,
        examinations=examinations,
        finding_types=finding_types,
        findings=findings,
        indication_types=indication_types,
        indications=indications,
        information_sources=information_sources,
        intervention_types=intervention_types,
        interventions=interventions,
        unit_types=unit_types,
        units=units,
    )
    return dataset


def interface2dataset(
    patient_interface: PatientInterface,
) -> InterfaceExportDataset:
    ################ KNOWLEDGE BASE
    # kb = patient_interface.knowledge_base

    ################ LEDGER
    ledger = patient_interface.patient_ledger
    ledger_dataset = ledger2dataset(ledger=ledger)
    kb_dataset = kb2dataset(kb=patient_interface.knowledge_base)

    dataset = InterfaceExportDataset(
        knowledge_base=kb_dataset,
        patient_ledger=ledger_dataset,
    )
    return dataset
