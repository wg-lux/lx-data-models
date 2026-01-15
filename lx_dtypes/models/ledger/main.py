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
from .p_indication import (
    LPIndicationDjangoLookupType,
    LPIndicationLookupType,
    l_p_indication_ddicts,
    l_p_indication_django_lookup,
    l_p_indication_django_models,
    l_p_indication_lookup,
    l_p_indication_models,
)


class LedgerModelsLookupType(
    LCenterLookupType,
    LPExaminationLookupType,
    LExaminerLookupType,
    LPFindingLookupType,
    LPIndicationLookupType,
):
    pass


ledger_models_lookup = LedgerModelsLookupType(
    **l_center_lookup,
    **l_p_examination_lookup,
    **l_examiner_lookup,
    **l_p_finding_lookup,
    **l_p_indication_lookup,
)


class LedgerModelsDjangoLookupType(
    LCenterDjangoLookupType,
    LPExaminationDjangoLookupType,
    LExaminerDjangoLookupType,
    LPFindingDjangoLookupType,
    LPIndicationDjangoLookupType,
):
    pass


ledger_models_django_lookup: LedgerModelsDjangoLookupType = (
    LedgerModelsDjangoLookupType(
        **l_center_django_lookup,
        **l_p_examination_django_lookup,
        **l_examiner_django_lookup,
        **l_p_finding_django_lookup,
        **l_p_indication_django_lookup,
    )
)

L_MODELS = Union[
    l_center_models,
    l_p_examination_models,
    l_examiner_models,
    l_p_finding_models,
    l_p_indication_models,
]

L_MODELS_DJANGO = Union[
    l_center_django_models,
    l_p_examination_django_models,
    l_examiner_django_models,
    l_p_finding_django_models,
    l_p_indication_django_models,
]

L_DDICTS = Union[
    l_center_ddicts,
    l_p_examination_ddicts,
    l_examiner_ddicts,
    l_p_finding_ddicts,
    l_p_indication_ddicts,
]
L_MODEL_NAMES_LITERAL = Literal[
    "Center", "Examiner", "PExamination", "PFinding", "PIndication"
]

L_MODEL_NAMES_ORDERED: List[L_MODEL_NAMES_LITERAL] = [
    "Center",
    "Examiner",
    "PExamination",
    "PFinding",
    "PIndication",
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
