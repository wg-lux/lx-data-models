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


class LedgerModelsLookupType(
    LCenterLookupType,
):
    pass


ledger_models_lookup = LedgerModelsLookupType(
    **l_center_lookup,
)


class LedgerModelsDjangoLookupType(LCenterDjangoLookupType):
    pass


ledger_models_django_lookup: LedgerModelsDjangoLookupType = (
    LedgerModelsDjangoLookupType(
        **l_center_django_lookup,
    )
)

L_MODELS = Union[l_center_models,]

L_MODELS_DJANGO = Union[l_center_django_models,]

L_DDICTS = Union[l_center_ddicts,]

L_MODEL_NAMES_LITERAL = Literal["Center", "Examiner"]

L_MODEL_NAMES_ORDERED: List[L_MODEL_NAMES_LITERAL] = ["Center", "Examiner"]
