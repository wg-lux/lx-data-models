from typing import TypedDict, Union

from .DataDict import PExaminationDataDict
from .Django import PExaminationDjango
from .Pydantic import PExamination


class LPExaminationDjangoLookupType(TypedDict):
    PExamination: type[PExaminationDjango]


l_p_examination_django_lookup = LPExaminationDjangoLookupType(
    PExamination=PExaminationDjango,
)


class LPExaminationLookupType(TypedDict):
    PExamination: type[PExamination]
    PExaminationDataDict: type[PExaminationDataDict]


l_p_examination_lookup = LPExaminationLookupType(
    PExamination=PExamination,
    PExaminationDataDict=PExaminationDataDict,
)

l_p_examination_models = Union[PExamination,]
l_p_examination_ddicts = Union[PExaminationDataDict,]
l_p_examination_django_models = Union[PExaminationDjango,]

__all__ = [
    "PExamination",
    "PExaminationDataDict",
    "l_p_examination_django_models",
    "l_p_examination_django_lookup",
    "LPExaminationDjangoLookupType",
    "l_p_examination_lookup",
    "LPExaminationLookupType",
    "l_p_examination_models",
    "l_p_examination_ddicts",
]
