"""Canonical Pydantic ledger registry; no Django adapters are imported."""

from typing import Literal, Union

from .case import LCaseLookupType, l_case_ddicts, l_case_lookup, l_case_models
from .center import LCenterLookupType, l_center_ddicts, l_center_lookup, l_center_models
from .examiner import (
    LExaminerLookupType,
    l_examiner_ddicts,
    l_examiner_lookup,
    l_examiner_models,
)
from .medical import (
    LMedicalLookupType,
    l_medical_ddicts,
    l_medical_lookup,
    l_medical_models,
)
from .p_electrical_application import (
    LPElectricalApplicationLookupType,
    PElectricalApplication,
    PElectricalApplicationDataDict,
    PElectricalCurveComparison,
    PElectricalCurveComparisonDataDict,
)
from .p_examination import (
    LPExaminationLookupType,
    l_p_examination_ddicts,
    l_p_examination_lookup,
    l_p_examination_models,
)
from .p_finding import (
    LPFindingLookupType,
    l_p_finding_ddicts,
    l_p_finding_lookup,
    l_p_finding_models,
)
from .p_finding_classification_choice import (
    LPFindingClassificationChoiceLookupType,
    l_p_finding_classification_choice_ddicts,
    l_p_finding_classification_choice_lookup,
    l_p_finding_classification_choice_models,
)
from .p_finding_classification_choice_descriptor import (
    LPFindingClassificationChoiceDescriptorLookupType,
    l_p_finding_classification_choice_descriptor_ddicts,
    l_p_finding_classification_choice_descriptor_lookup,
    l_p_finding_classification_choice_descriptor_models,
)
from .p_finding_classifications import (
    LPFindingClassificationsLookupType,
    l_p_finding_classifications_ddicts,
    l_p_finding_classifications_lookup,
    l_p_finding_classifications_models,
)
from .p_indication import (
    LPIndicationLookupType,
    l_p_indication_ddicts,
    l_p_indication_lookup,
    l_p_indication_models,
)
from .p_indication_classification import (
    LPIndicationClassificationLookupType,
    l_p_indication_classification_ddicts,
    l_p_indication_classification_lookup,
    l_p_indication_classification_models,
)
from .p_indication_classification_descriptor import (
    LPIndicationClassificationDescriptorLookupType,
    l_p_indication_classification_descriptor_ddicts,
    l_p_indication_classification_descriptor_lookup,
    l_p_indication_classification_descriptor_models,
)
from .p_intervention import (
    LPFindingInterventionLookupType,
    l_p_finding_intervention_ddicts,
    l_p_finding_intervention_lookup,
    l_p_finding_intervention_models,
)
from .p_interventions import (
    LPFindingInterventionsLookupType,
    l_p_finding_interventions_ddicts,
    l_p_finding_interventions_lookup,
    l_p_finding_interventions_models,
)
from .p_time_offset import LPTimeOffsetLookupType, PTimeOffset, PTimeOffsetDataDict
from .p_video import (
    LPVideoLookupType,
    l_p_video_ddicts,
    l_p_video_lookup,
    l_p_video_models,
)
from .patient import (
    LPatientLookupType,
    l_patient_ddicts,
    l_patient_lookup,
    l_patient_models,
)
from .report import LReportLookupType, l_report_ddicts, l_report_lookup, l_report_models
from .video_file import (
    LVidFileLookupType,
    l_vid_file_ddicts,
    l_vid_file_lookup,
    l_vid_file_models,
)


class LedgerModelsLookupType(
    LPTimeOffsetLookupType,
    LPElectricalApplicationLookupType,
    LCenterLookupType,
    LPExaminationLookupType,
    LReportLookupType,
    LCaseLookupType,
    LExaminerLookupType,
    LPFindingLookupType,
    LPIndicationLookupType,
    LPIndicationClassificationLookupType,
    LPIndicationClassificationDescriptorLookupType,
    LPFindingClassificationsLookupType,
    LPFindingClassificationChoiceLookupType,
    LPFindingClassificationChoiceDescriptorLookupType,
    LPFindingInterventionsLookupType,
    LPFindingInterventionLookupType,
    LPatientLookupType,
    LPVideoLookupType,
    LVidFileLookupType,
    LMedicalLookupType,
):
    pass


ledger_models_lookup = LedgerModelsLookupType(
    PTimeOffset=PTimeOffset,
    PElectricalApplication=PElectricalApplication,
    PElectricalCurveComparison=PElectricalCurveComparison,
    **l_center_lookup,
    **l_p_examination_lookup,
    **l_case_lookup,
    **l_report_lookup,
    **l_examiner_lookup,
    **l_p_finding_lookup,
    **l_p_indication_lookup,
    **l_p_indication_classification_lookup,
    **l_p_indication_classification_descriptor_lookup,
    **l_p_finding_classifications_lookup,
    **l_p_finding_classification_choice_lookup,
    **l_p_finding_classification_choice_descriptor_lookup,
    **l_p_finding_interventions_lookup,
    **l_p_finding_intervention_lookup,
    **l_patient_lookup,
    **l_p_video_lookup,
    **l_vid_file_lookup,
    **l_medical_lookup,
)


L_MODELS = Union[
    PTimeOffset,
    PElectricalApplication,
    PElectricalCurveComparison,
    l_center_models,
    l_p_examination_models,
    l_case_models,
    l_report_models,
    l_examiner_models,
    l_p_finding_models,
    l_p_indication_models,
    l_p_indication_classification_models,
    l_p_indication_classification_descriptor_models,
    l_p_finding_classifications_models,
    l_p_finding_classification_choice_models,
    l_p_finding_classification_choice_descriptor_models,
    l_p_finding_interventions_models,
    l_p_finding_intervention_models,
    l_vid_file_models,
    l_patient_models,
    l_p_video_models,
    l_medical_models,
]


L_DDICTS = Union[
    PTimeOffsetDataDict,
    PElectricalApplicationDataDict,
    PElectricalCurveComparisonDataDict,
    l_center_ddicts,
    l_p_examination_ddicts,
    l_case_ddicts,
    l_examiner_ddicts,
    l_p_finding_ddicts,
    l_p_indication_ddicts,
    l_p_indication_classification_ddicts,
    l_p_indication_classification_descriptor_ddicts,
    l_p_finding_classifications_ddicts,
    l_p_finding_classification_choice_ddicts,
    l_p_finding_classification_choice_descriptor_ddicts,
    l_p_finding_interventions_ddicts,
    l_p_finding_intervention_ddicts,
    l_patient_ddicts,
    l_vid_file_ddicts,
    l_report_ddicts,
    l_p_video_ddicts,
    l_medical_ddicts,
]


L_MODEL_NAMES_LITERAL = Literal[
    "PTimeOffset",
    "PElectricalApplication",
    "PElectricalCurveComparison",
    "Center",
    "Examiner",
    "Patient",
    "PExamination",
    "Case",
    "Report",
    "PFinding",
    "PIndication",
    "PIndicationClassification",
    "PIndicationClassificationDescriptor",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingClassificationChoiceDescriptor",
    "PFindingInterventions",
    "PFindingIntervention",
    "VideoFile",
    "PatientVideoFile",
    "PatientDisease",
    "PatientEvent",
    "PatientLabSample",
    "PatientLabValue",
    "PatientMedication",
    "PatientMedicationSchedule",
    "PatientMedicalLedger",
]


L_MODEL_NAMES_ORDERED: list[L_MODEL_NAMES_LITERAL] = [
    "PTimeOffset",
    "PElectricalApplication",
    "PElectricalCurveComparison",
    "Center",
    "Examiner",
    "Patient",
    "PExamination",
    "Case",
    "Report",
    "PFinding",
    "PIndication",
    "PIndicationClassification",
    "PIndicationClassificationDescriptor",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingClassificationChoiceDescriptor",
    "PFindingInterventions",
    "PFindingIntervention",
    "VideoFile",
    "PatientVideoFile",
    "PatientDisease",
    "PatientEvent",
    "PatientLabSample",
    "PatientLabValue",
    "PatientMedication",
    "PatientMedicationSchedule",
    "PatientMedicalLedger",
]


__all__ = [
    "L_DDICTS",
    "L_MODELS",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "LedgerModelsLookupType",
    "ledger_models_lookup",
]
