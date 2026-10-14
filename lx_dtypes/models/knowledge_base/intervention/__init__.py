from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeAlias, TypedDict, Union

if TYPE_CHECKING:
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
if TYPE_CHECKING:

    class KbInterventionDjangoLookupType(TypedDict):
        Intervention: type[InterventionDjango]
        InterventionType: type[InterventionTypeDjango]

    kb_intervention_django_lookup: KbInterventionDjangoLookupType
    kb_intervention_django_models: TypeAlias = Union[
        InterventionDjango, InterventionTypeDjango
    ]
kb_intervention_models: TypeAlias = Union[Intervention, InterventionType]

kb_intervention_ddicts: TypeAlias = Union[
    InterventionDataDict, InterventionTypeDataDict
]

__all__ = [
    "Intervention",
    "InterventionDataDict",
    "InterventionType",
    "InterventionTypeDataDict",
    "KbInterventionDjangoLookupType",
    "KbInterventionLookupType",
    "kb_intervention_ddicts",
    "kb_intervention_django_lookup",
    "kb_intervention_django_models",
    "kb_intervention_lookup",
    "kb_intervention_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "InterventionDjango",
        "InterventionTypeDjango",
        "KbInterventionDjangoLookupType",
        "kb_intervention_django_lookup",
        "kb_intervention_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .InterventionDjango import InterventionDjango
    from .InterventionTypeDjango import InterventionTypeDjango

    class KbInterventionDjangoLookupType(TypedDict):
        Intervention: type[InterventionDjango]
        InterventionType: type[InterventionTypeDjango]

    exports = {
        "InterventionDjango": InterventionDjango,
        "InterventionTypeDjango": InterventionTypeDjango,
        "KbInterventionDjangoLookupType": KbInterventionDjangoLookupType,
        "kb_intervention_django_lookup": KbInterventionDjangoLookupType(
            Intervention=InterventionDjango,
            InterventionType=InterventionTypeDjango,
        ),
        "kb_intervention_django_models": InterventionDjango | InterventionTypeDjango,
    }
    globals().update(exports)
    return exports[name]
