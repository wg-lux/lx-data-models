from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PExaminationDataDict
from .Pydantic import PExamination

if TYPE_CHECKING:
    from .Django import PExaminationDjango

    l_p_examination_django_lookup: LPExaminationDjangoLookupType
    type l_p_examination_django_models = PExaminationDjango


class LPExaminationDjangoLookupType(TypedDict):
    PExamination: type[PExaminationDjango]


class LPExaminationLookupType(TypedDict):
    PExamination: type[PExamination]
    PExaminationDataDict: type[PExaminationDataDict]


l_p_examination_lookup = LPExaminationLookupType(
    PExamination=PExamination,
    PExaminationDataDict=PExaminationDataDict,
)

l_p_examination_models = Union[PExamination,]
l_p_examination_ddicts = Union[PExaminationDataDict,]

__all__ = [
    "LPExaminationDjangoLookupType",
    "LPExaminationLookupType",
    "PExamination",
    "PExaminationDataDict",
    "l_p_examination_ddicts",
    "l_p_examination_django_lookup",
    "l_p_examination_django_models",
    "l_p_examination_lookup",
    "l_p_examination_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PExaminationDjango",
        "l_p_examination_django_lookup",
        "l_p_examination_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PExaminationDjango

    exports: dict[str, object] = {
        "PExaminationDjango": PExaminationDjango,
        "l_p_examination_django_lookup": LPExaminationDjangoLookupType(
            PExamination=PExaminationDjango
        ),
        "l_p_examination_django_models": PExaminationDjango,
    }
    globals().update(exports)
    return exports[name]
