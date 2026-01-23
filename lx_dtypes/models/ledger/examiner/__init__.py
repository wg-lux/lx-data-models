from typing import TypedDict, Union

from .DataDict import ExaminerDataDict
from .Django import ExaminerDjango
from .Pydantic import Examiner


class LExaminerDjangoLookupType(TypedDict):
    Examiner: type[ExaminerDjango]


l_examiner_django_lookup = LExaminerDjangoLookupType(
    Examiner=ExaminerDjango,
)


class LExaminerLookupType(TypedDict):
    Examiner: type[Examiner]
    ExaminerDataDict: type[ExaminerDataDict]


l_examiner_lookup = LExaminerLookupType(
    Examiner=Examiner,
    ExaminerDataDict=ExaminerDataDict,
)

l_examiner_models = Union[Examiner,]
l_examiner_ddicts = Union[ExaminerDataDict,]
l_examiner_django_models = Union[ExaminerDjango,]

__all__ = [
    "Examiner",
    "ExaminerDataDict",
    "l_examiner_django_models",
    "l_examiner_django_lookup",
    "LExaminerDjangoLookupType",
    "l_examiner_lookup",
    "LExaminerLookupType",
    "l_examiner_models",
    "l_examiner_ddicts",
]
