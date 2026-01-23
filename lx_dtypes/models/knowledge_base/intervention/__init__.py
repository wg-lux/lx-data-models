from typing import TypedDict, Union

from lx_dtypes.models.knowledge_base.intervention.InterventionDjango import (
    InterventionDjango,
)
from lx_dtypes.models.knowledge_base.intervention.InterventionTypeDjango import (
    InterventionTypeDjango,
)

from .Intervention import Intervention
from .InterventionDataDict import InterventionDataDict
from .InterventionType import InterventionType
from .InterventionTypeDataDict import InterventionTypeDataDict


class KbInterventionDjangoLookupType(TypedDict):
    Intervention: type[InterventionDjango]
    InterventionType: type[InterventionTypeDjango]


kb_intervention_django_lookup = KbInterventionDjangoLookupType(
    Intervention=InterventionDjango,
    InterventionType=InterventionTypeDjango,
)


class KbInterventionLookupType(TypedDict):
    Intervention: type[Intervention]
    InterventionDataDict: type[InterventionDataDict]
    InterventionType: type[InterventionType]
    InterventionTypeDataDict: type[InterventionTypeDataDict]


kb_intervention_lookup = KbInterventionLookupType(
    Intervention=Intervention,
    InterventionDataDict=InterventionDataDict,
    InterventionTypeDataDict=InterventionTypeDataDict,
    InterventionType=InterventionType,
)
kb_intervention_django_models = Union[
    InterventionDjango,
    InterventionTypeDjango,
]
kb_intervention_models = Union[
    Intervention,
    InterventionType,
]

kb_intervention_ddicts = Union[
    InterventionDataDict,
    InterventionTypeDataDict,
]

__all__ = [
    "Intervention",
    "InterventionDataDict",
    "InterventionType",
    "InterventionTypeDataDict",
    "kb_intervention_lookup",
    "KbInterventionLookupType",
    "kb_intervention_models",
    "kb_intervention_ddicts",
    "kb_intervention_django_models",
    "kb_intervention_django_lookup",
    "KbInterventionDjangoLookupType",
]
