from typing import List, Literal, Union

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
    LExaminerLookupType,
    LPFindingLookupType,
    LPIndicationLookupType,
    LPFindingClassificationsLookupType,
    LPFindingClassificationChoiceLookupType,
    LPFindingClassificationChoiceDescriptorLookupType,
    LPFindingInterventionsLookupType,
    LPFindingInterventionLookupType,
    LPatientLookupType,
):
    pass


ledger_models_lookup = LedgerModelsLookupType(
    **l_center_lookup,
    **l_p_examination_lookup,
    **l_examiner_lookup,
    **l_p_finding_lookup,
    **l_p_indication_lookup,
    **l_p_finding_classifications_lookup,
    **l_p_finding_classification_choice_lookup,
    **l_p_finding_classification_choice_descriptor_lookup,
    **l_p_finding_interventions_lookup,
    **l_p_finding_intervention_lookup,
    **l_patient_lookup,
)


class LedgerModelsDjangoLookupType(
    LCenterDjangoLookupType,
    LPExaminationDjangoLookupType,
    LExaminerDjangoLookupType,
    LPFindingDjangoLookupType,
    LPIndicationDjangoLookupType,
    LPFindingClassificationsDjangoLookupType,
    LPFindingClassificationChoiceDjangoLookupType,
    LPFindingClassificationChoiceDescriptorDjangoLookupType,
    LPFindingInterventionsDjangoLookupType,
    LPFindingInterventionDjangoLookupType,
    LPatientDjangoLookupType,
):
    pass


ledger_models_django_lookup: LedgerModelsDjangoLookupType = (
    LedgerModelsDjangoLookupType(
        **l_center_django_lookup,
        **l_p_examination_django_lookup,
        **l_examiner_django_lookup,
        **l_p_finding_django_lookup,
        **l_p_indication_django_lookup,
        **l_p_finding_classifications_django_lookup,
        **l_p_finding_classification_choice_django_lookup,
        **l_p_finding_classification_choice_descriptor_django_lookup,
        **l_p_finding_interventions_django_lookup,
        **l_p_finding_intervention_django_lookup,
        **l_patient_django_lookup,
    )
)

L_MODELS = Union[
    l_center_models,
    l_p_examination_models,
    l_examiner_models,
    l_p_finding_models,
    l_p_indication_models,
    l_p_finding_classifications_models,
    l_p_finding_classification_choice_models,
    l_p_finding_classification_choice_descriptor_models,
    l_p_finding_interventions_models,
    l_p_finding_intervention_models,
    l_patient_models,
]

L_MODELS_DJANGO = Union[
    l_center_django_models,
    l_p_examination_django_models,
    l_examiner_django_models,
    l_p_finding_django_models,
    l_p_indication_django_models,
    l_p_finding_classifications_django_models,
    l_p_finding_classification_choice_django_models,
    l_p_finding_classification_choice_descriptor_django_models,
    l_p_finding_interventions_django_models,
    l_p_finding_intervention_django_models,
    l_patient_django_models,
]

L_DDICTS = Union[
    l_center_ddicts,
    l_p_examination_ddicts,
    l_examiner_ddicts,
    l_p_finding_ddicts,
    l_p_indication_ddicts,
    l_p_finding_classifications_ddicts,
    l_p_finding_classification_choice_ddicts,
    l_p_finding_classification_choice_descriptor_ddicts,
    l_p_finding_interventions_ddicts,
    l_p_finding_intervention_ddicts,
    l_patient_ddicts,
]
L_MODEL_NAMES_LITERAL = Literal[
    "Center",
    "Examiner",
    "PExamination",
    "PFinding",
    "PIndication",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingInterventions",
    "PFindingIntervention",
]

L_MODEL_NAMES_ORDERED: List[L_MODEL_NAMES_LITERAL] = [
    "Center",
    "Examiner",
    "PExamination",
    "PFinding",
    "PIndication",
    "PFindingClassifications",
    "PFindingClassificationChoice",
    "PFindingInterventions",
    "PFindingIntervention",
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
