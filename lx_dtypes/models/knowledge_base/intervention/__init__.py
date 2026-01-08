from typing import TypedDict, Union

from .Intervention import Intervention
from .InterventionDataDict import InterventionDataDict
from .InterventionType import InterventionType
from .InterventionTypeDataDict import InterventionTypeDataDict


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
]
