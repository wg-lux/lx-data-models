from typing import List, Literal, Union

from .case import (
    LCaseLookupType,
    l_case_ddicts,
    l_case_lookup,
    l_case_models,
)

from .center import (
    LCenterDjangoLookupType,
    LCenterLookupType,
    l_center_ddicts,
    l_center_django_lookup,
    l_center_django_models,
    l_center_lookup,
    l_center_models,
)
from .examiner import (
    LExaminerDjangoLookupType,
    LExaminerLookupType,
    l_examiner_ddicts,
    l_examiner_django_lookup,
    l_examiner_django_models,
    l_examiner_lookup,
    l_examiner_models,
)
from .p_examination import (
    LPExaminationDjangoLookupType,
    LPExaminationLookupType,
    l_p_examination_ddicts,
    l_p_examination_django_lookup,
    l_p_examination_django_models,
    l_p_examination_lookup,
    l_p_examination_models,
)
from .p_finding import (
    LPFindingDjangoLookupType,
    LPFindingLookupType,
    l_p_finding_ddicts,
    l_p_finding_django_lookup,
    l_p_finding_django_models,
    l_p_finding_lookup,
    l_p_finding_models,
)
from .p_finding_classification_choice import (
    LPFindingClassificationChoiceDjangoLookupType,
    LPFindingClassificationChoiceLookupType,
    l_p_finding_classification_choice_ddicts,
    l_p_finding_classification_choice_django_lookup,
    l_p_finding_classification_choice_django_models,
    l_p_finding_classification_choice_lookup,
    l_p_finding_classification_choice_models,
)
from .p_finding_classification_choice_descriptor import (
    LPFindingClassificationChoiceDescriptorDjangoLookupType,
    LPFindingClassificationChoiceDescriptorLookupType,
    l_p_finding_classification_choice_descriptor_ddicts,
    l_p_finding_classification_choice_descriptor_django_lookup,
    l_p_finding_classification_choice_descriptor_django_models,
    l_p_finding_classification_choice_descriptor_lookup,
    l_p_finding_classification_choice_descriptor_models,
)
from .p_finding_classifications import (
    LPFindingClassificationsDjangoLookupType,
    LPFindingClassificationsLookupType,
    l_p_finding_classifications_ddicts,
    l_p_finding_classifications_django_lookup,
    l_p_finding_classifications_django_models,
    l_p_finding_classifications_lookup,
    l_p_finding_classifications_models,
)
from .p_indication import (
    LPIndicationDjangoLookupType,
    LPIndicationLookupType,
    l_p_indication_ddicts,
    l_p_indication_django_lookup,
    l_p_indication_django_models,
    l_p_indication_lookup,
    l_p_indication_models,
)
from .p_indication_classification import (
    LPIndicationClassificationDjangoLookupType,
    LPIndicationClassificationLookupType,
    l_p_indication_classification_ddicts,
    l_p_indication_classification_django_lookup,
    l_p_indication_classification_django_models,
    l_p_indication_classification_lookup,
    l_p_indication_classification_models,
)
from .p_indication_classification_descriptor import (
    LPIndicationClassificationDescriptorDjangoLookupType,
    LPIndicationClassificationDescriptorLookupType,
    l_p_indication_classification_descriptor_ddicts,
    l_p_indication_classification_descriptor_django_lookup,
    l_p_indication_classification_descriptor_django_models,
    l_p_indication_classification_descriptor_lookup,
    l_p_indication_classification_descriptor_models,
)
from .p_intervention import (
    LPFindingInterventionDjangoLookupType,
    LPFindingInterventionLookupType,
    l_p_finding_intervention_ddicts,
    l_p_finding_intervention_django_lookup,
    l_p_finding_intervention_django_models,
    l_p_finding_intervention_lookup,
    l_p_finding_intervention_models,
)
from .p_interventions import (
    LPFindingInterventionsDjangoLookupType,
    LPFindingInterventionsLookupType,
    l_p_finding_interventions_ddicts,
    l_p_finding_interventions_django_lookup,
    l_p_finding_interventions_django_models,
    l_p_finding_interventions_lookup,
    l_p_finding_interventions_models,
)
from .p_video import (
    LPVideoLookupType,
    l_p_video_ddicts,
    # LPVideoDjangoLookupType, # TODO
    # l_p_video_django_lookup, # TODO
    # l_p_video_django_models, # TODO
    l_p_video_lookup,
    l_p_video_models,
)
from .patient import (
    LPatientDjangoLookupType,
    LPatientLookupType,
    l_patient_ddicts,
    l_patient_django_lookup,
    l_patient_django_models,
    l_patient_lookup,
    l_patient_models,
)


class LedgerModelsLookupType(
    LCenterLookupType,
    LPExaminationLookupType,
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
):
    pass


ledger_models_lookup = LedgerModelsLookupType(
    **l_center_lookup,
    **l_p_examination_lookup,
    **l_case_lookup,
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
)


class LedgerModelsDjangoLookupType(
    LCenterDjangoLookupType,
    LPExaminationDjangoLookupType,
    LExaminerDjangoLookupType,
    LPFindingDjangoLookupType,
    LPIndicationDjangoLookupType,
    LPIndicationClassificationDjangoLookupType,
    LPIndicationClassificationDescriptorDjangoLookupType,
    LPFindingClassificationsDjangoLookupType,
    LPFindingClassificationChoiceDjangoLookupType,
    LPFindingClassificationChoiceDescriptorDjangoLookupType,
    LPFindingInterventionsDjangoLookupType,
    LPFindingInterventionDjangoLookupType,
    LPatientDjangoLookupType,
    # LPVideoDjangoLookupType, # TODO
):
    pass


ledger_models_django_lookup: LedgerModelsDjangoLookupType = (
    LedgerModelsDjangoLookupType(
        **l_center_django_lookup,
        **l_p_examination_django_lookup,
        **l_examiner_django_lookup,
        **l_p_finding_django_lookup,
        **l_p_indication_django_lookup,
        **l_p_indication_classification_django_lookup,
        **l_p_indication_classification_descriptor_django_lookup,
        **l_p_finding_classifications_django_lookup,
        **l_p_finding_classification_choice_django_lookup,
        **l_p_finding_classification_choice_descriptor_django_lookup,
        **l_p_finding_interventions_django_lookup,
        **l_p_finding_intervention_django_lookup,
        **l_patient_django_lookup,
        # **l_p_video_django_lookup, # TODO
    )
)

L_MODELS = Union[
    l_center_models,
    l_p_examination_models,
    l_case_models,
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
    l_patient_models,
    l_p_video_models,
]

L_MODELS_DJANGO = Union[
    l_center_django_models,
    l_p_examination_django_models,
    l_examiner_django_models,
    l_p_finding_django_models,
    l_p_indication_django_models,
    l_p_indication_classification_django_models,
    l_p_indication_classification_descriptor_django_models,
    l_p_finding_classifications_django_models,
    l_p_finding_classification_choice_django_models,
    l_p_finding_classification_choice_descriptor_django_models,
    l_p_finding_interventions_django_models,
    l_p_finding_intervention_django_models,
    l_patient_django_models,
    # l_p_video_django_models, # TODO
]

L_DDICTS = Union[
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
    l_p_video_ddicts,
]
L_MODEL_NAMES_LITERAL = Literal[
    "Center",
    "Examiner",
    "Patient",
    "PExamination",
    "Case",
    "PFinding",
    "PIndication",
    "PIndicationClassification",
    "PIndicationClassificationDescriptor",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingInterventions",
    "PFindingIntervention",
    "PatientVideoFile",
    "RawPatientVideoFile",
]

L_MODEL_NAMES_ORDERED: List[L_MODEL_NAMES_LITERAL] = [
    "Center",
    "Examiner",
    "Patient",
    "PExamination",
    "Case",
    "PFinding",
    "PIndication",
    "PIndicationClassification",
    "PIndicationClassificationDescriptor",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingInterventions",
    "PFindingIntervention",
    "PatientVideoFile",
    "RawPatientVideoFile",
]

__all__ = [
    "L_MODELS",
    "L_MODELS_DJANGO",
    "L_DDICTS",
    "ledger_models_lookup",
    "LedgerModelsLookupType",
    "ledger_models_django_lookup",
    "LedgerModelsDjangoLookupType",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
]
