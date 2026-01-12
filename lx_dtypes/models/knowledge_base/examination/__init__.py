from typing import TypedDict, Union

from .Examination import Examination
from .ExaminationDataDict import ExaminationDataDict
from .ExaminationDjango import ExaminationDjango
from .ExaminationType import ExaminationType
from .ExaminationTypeDataDict import ExaminationTypeDataDict
from .ExaminationTypeDjango import ExaminationTypeDjango


class KbExaminationDjangoLookupType(TypedDict):
    Examination: type[ExaminationDjango]
    ExaminationType: type[ExaminationTypeDjango]


kb_examination_django_lookup = KbExaminationDjangoLookupType(
    Examination=ExaminationDjango,
    ExaminationType=ExaminationTypeDjango,
)


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
