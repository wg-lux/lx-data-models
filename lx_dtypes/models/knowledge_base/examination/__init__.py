from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from .Examination import Examination
from .ExaminationDataDict import ExaminationDataDict
from .ExaminationType import ExaminationType
from .ExaminationTypeDataDict import ExaminationTypeDataDict
if TYPE_CHECKING:
    from .ExaminationDjango import ExaminationDjango
    from .ExaminationTypeDjango import ExaminationTypeDjango


class KbExaminationLookupType(TypedDict):
    Examination: type[Examination]
    ExaminationDataDict: type[ExaminationDataDict]
    ExaminationType: type[ExaminationType]
    ExaminationTypeDataDict: type[ExaminationTypeDataDict]


kb_examination_lookup = KbExaminationLookupType(
    Examination=Examination,
    ExaminationDataDict=ExaminationDataDict,
    ExaminationType=ExaminationType,
    ExaminationTypeDataDict=ExaminationTypeDataDict,
)

kb_examination_models = Union[
    Examination,
    ExaminationType,
]

kb_examination_ddicts = Union[
    ExaminationDataDict,
    ExaminationTypeDataDict,
]

if TYPE_CHECKING:
    class KbExaminationDjangoLookupType(TypedDict):
        Examination: type[ExaminationDjango]
        ExaminationType: type[ExaminationTypeDjango]

    kb_examination_django_lookup: KbExaminationDjangoLookupType
    kb_examination_django_models = Union[
        ExaminationDjango,
        ExaminationTypeDjango,
    ]

__all__ = [
    "Examination",
    "ExaminationDataDict",
    "ExaminationType",
    "ExaminationTypeDataDict",
    "kb_examination_lookup",
    "KbExaminationLookupType",
    "kb_examination_models",
    "kb_examination_ddicts",
    "kb_examination_django_models",
    "kb_examination_django_lookup",
    "KbExaminationDjangoLookupType",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "ExaminationDjango",
        "ExaminationTypeDjango",
        "KbExaminationDjangoLookupType",
        "kb_examination_django_lookup",
        "kb_examination_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .ExaminationDjango import ExaminationDjango
    from .ExaminationTypeDjango import ExaminationTypeDjango

    class KbExaminationDjangoLookupType(TypedDict):
        Examination: type[ExaminationDjango]
        ExaminationType: type[ExaminationTypeDjango]

    exports = {
        "ExaminationDjango": ExaminationDjango,
        "ExaminationTypeDjango": ExaminationTypeDjango,
        "KbExaminationDjangoLookupType": KbExaminationDjangoLookupType,
        "kb_examination_django_lookup": KbExaminationDjangoLookupType(
            Examination=ExaminationDjango,
            ExaminationType=ExaminationTypeDjango,
        ),
        "kb_examination_django_models": Union[
            ExaminationDjango,
            ExaminationTypeDjango,
        ],
    }
    globals().update(exports)
    return exports[name]
