from typing import TypedDict, Union

from .Examination import Examination
from .ExaminationDataDict import ExaminationDataDict
from .ExaminationType import ExaminationType
from .ExaminationTypeDataDict import ExaminationTypeDataDict


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

__all__ = [
    "Examination",
    "ExaminationDataDict",
    "ExaminationType",
    "ExaminationTypeDataDict",
    "kb_examination_lookup",
    "KbExaminationLookupType",
    "kb_examination_models",
    "kb_examination_ddicts",
]
