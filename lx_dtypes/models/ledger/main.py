from typing import Union

from .center import (
    LCenterDjangoLookupType,
    l_center_django_lookup,
    l_center_django_models,
)
from .examiner import (
    LExaminerDjangoLookupType,
    l_examiner_django_lookup,
    l_examiner_django_models,
)
from .p_examination import (
    LPExaminationDjangoLookupType,
    l_p_examination_django_lookup,
    l_p_examination_django_models,
)
from .p_finding import (
    LPFindingDjangoLookupType,
    l_p_finding_django_lookup,
    l_p_finding_django_models,
)
from .p_finding_classification_choice import (
    LPFindingClassificationChoiceDjangoLookupType,
    l_p_finding_classification_choice_django_lookup,
    l_p_finding_classification_choice_django_models,
)
from .p_finding_classification_choice_descriptor import (
    LPFindingClassificationChoiceDescriptorDjangoLookupType,
    l_p_finding_classification_choice_descriptor_django_lookup,
    l_p_finding_classification_choice_descriptor_django_models,
)
from .p_finding_classifications import (
    LPFindingClassificationsDjangoLookupType,
    l_p_finding_classifications_django_lookup,
    l_p_finding_classifications_django_models,
)
from .p_indication import (
    LPIndicationDjangoLookupType,
    l_p_indication_django_lookup,
    l_p_indication_django_models,
)
from .p_indication_classification import (
    LPIndicationClassificationDjangoLookupType,
    l_p_indication_classification_django_lookup,
    l_p_indication_classification_django_models,
)
from .p_indication_classification_descriptor import (
    LPIndicationClassificationDescriptorDjangoLookupType,
    l_p_indication_classification_descriptor_django_lookup,
    l_p_indication_classification_descriptor_django_models,
)
from .p_intervention import (
    LPFindingInterventionDjangoLookupType,
    l_p_finding_intervention_django_lookup,
    l_p_finding_intervention_django_models,
)
from .p_interventions import (
    LPFindingInterventionsDjangoLookupType,
    l_p_finding_interventions_django_lookup,
    l_p_finding_interventions_django_models,
)
from .patient import (
    LPatientDjangoLookupType,
    l_patient_django_lookup,
    l_patient_django_models,
)
from .pydantic_main import (
    L_DDICTS,
    L_MODEL_NAMES_LITERAL,
    L_MODEL_NAMES_ORDERED,
    L_MODELS,
    LedgerModelsLookupType,
    ledger_models_lookup,
)
from .video_file import (
    LVidFileDjangoLookupType,
    l_vid_file_django_lookup,
    l_vid_file_django_models,
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
    LVidFileDjangoLookupType,
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
        **l_vid_file_django_lookup,
        # **l_p_video_django_lookup, # TODO
    )
)


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
    l_vid_file_django_models,
    # l_p_video_django_models, # TODO
]


__all__ = [
    "L_DDICTS",
    "L_MODELS",
    "L_MODELS_DJANGO",
    "L_MODEL_NAMES_LITERAL",
    "L_MODEL_NAMES_ORDERED",
    "LedgerModelsDjangoLookupType",
    "LedgerModelsLookupType",
    "ledger_models_django_lookup",
    "ledger_models_lookup",
]
