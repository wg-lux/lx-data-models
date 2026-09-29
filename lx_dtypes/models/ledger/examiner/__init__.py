from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import ExaminerDataDict
from .Pydantic import Examiner

if TYPE_CHECKING:
    from .Django import ExaminerDjango

    class LExaminerDjangoLookupType(TypedDict):
        Examiner: type[ExaminerDjango]

    l_examiner_django_lookup: LExaminerDjangoLookupType
    type l_examiner_django_models = ExaminerDjango


class LExaminerLookupType(TypedDict):
    Examiner: type[Examiner]
    ExaminerDataDict: type[ExaminerDataDict]


l_examiner_lookup = LExaminerLookupType(
    Examiner=Examiner,
    ExaminerDataDict=ExaminerDataDict,
)

l_examiner_models = Union[Examiner,]
l_examiner_ddicts = Union[ExaminerDataDict,]

__all__ = [
    "Examiner",
    "ExaminerDataDict",
    "LExaminerDjangoLookupType",
    "LExaminerLookupType",
    "l_examiner_ddicts",
    "l_examiner_django_lookup",
    "l_examiner_django_models",
    "l_examiner_lookup",
    "l_examiner_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "ExaminerDjango",
        "LExaminerDjangoLookupType",
        "l_examiner_django_lookup",
        "l_examiner_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import ExaminerDjango

    class LExaminerDjangoLookupType(TypedDict):
        Examiner: type[ExaminerDjango]

    exports: dict[str, object] = {
        "ExaminerDjango": ExaminerDjango,
        "LExaminerDjangoLookupType": LExaminerDjangoLookupType,
        "l_examiner_django_lookup": LExaminerDjangoLookupType(Examiner=ExaminerDjango),
        "l_examiner_django_models": ExaminerDjango,
    }
    globals().update(exports)
    return exports[name]
