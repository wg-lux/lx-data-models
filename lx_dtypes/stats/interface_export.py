from typing import List

# import numpy as np
import pandas as pd
from pandera.typing.pandas import DataFrame

from lx_dtypes.models.examiner.examiner import ExaminerShallowDataDict
from lx_dtypes.models.patient.patient_classification_choice_descriptor import (
    PatientFindingClassificationChoiceDescriptorShallowDataDict,
)

# from lx_dtypes.models.patient.patient import PatientDataDictShallow
from lx_dtypes.models.patient.patient_examination import (
    PatientExaminationShallowDataDict,
)
from lx_dtypes.models.patient.patient_finding import PatientFindingShallowDataDict
from lx_dtypes.models.patient.patient_finding_classification_choice import (
    PatientFindingClassificationChoiceShallowDataDict,
)
from lx_dtypes.models.patient.patient_finding_classifications import (
    PatientFindingClassificationsShallowDataDict,
)
from lx_dtypes.models.patient_interface import PatientInterface
from lx_dtypes.models.shallow.center import CenterShallowDataDict

from .schemas import (
    CenterShallowSchema,
    ExaminerShallowSchema,
    PatientExaminationShallowSchema,
    PatientFindingClassificationChoiceDescriptorShallowSchema,
    PatientFindingClassificationChoiceShallowSchema,
    PatientFindingClassificationsShallowSchema,
    PatientFindingShallowSchema,
    PatientShallowSchema,
)


def ledger2dataset(
    patient_interface: PatientInterface,
) -> tuple[
    DataFrame[PatientShallowSchema],
    DataFrame[PatientExaminationShallowSchema],
    DataFrame[PatientFindingShallowSchema],
    DataFrame[PatientFindingClassificationsShallowSchema],
    DataFrame[PatientFindingClassificationChoiceShallowSchema],
    DataFrame[PatientFindingClassificationChoiceDescriptorShallowSchema],
    DataFrame[CenterShallowSchema],
    DataFrame[ExaminerShallowSchema],
]:
    ################ KNOWLEDGE BASE
    # kb = patient_interface.knowledge_base

    ################ LEDGER
    ledger = patient_interface.patient_ledger

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

    return (
        df_patients,
        df_examinations,
        df_findings,
        df_classifications,
        df_choices,
        df_descriptors,
        df_centers,
        df_examiners,
    )
