from typing import TypedDict, Union

from lx_dtypes.contrib.lx_django.models import (
    Citation,
    Classification,
    ClassificationChoice,
    ClassificationChoiceDescriptor,
    ClassificationType,
    Examination,
    ExaminationType,
    Finding,
    FindingType,
    Indication,
    IndicationType,
    InformationSource,
    Intervention,
    InterventionType,
    Unit,
    UnitType,
)

KB_DJANGO_MODEL_LIST = [
    Citation,
    Classification,
    ClassificationChoice,
    ClassificationChoiceDescriptor,
    ClassificationType,
    Examination,
    ExaminationType,
    Finding,
    FindingType,
    Indication,
    IndicationType,
    Intervention,
    InterventionType,
    Unit,
    UnitType,
    InformationSource,
]

KB_UNION_DJANGO_MODEL_LIST = Union[
    Citation,
    Classification,
    ClassificationChoice,
    ClassificationChoiceDescriptor,
    ClassificationType,
    Examination,
    ExaminationType,
    Finding,
    FindingType,
    Indication,
    IndicationType,
    Intervention,
    InterventionType,
    Unit,
    UnitType,
    InformationSource,
]

KB_UNION_DJANGO_MODEL_TYPE_LIST = Union[
    type[Citation],
    type[Classification],
    type[ClassificationChoice],
    type[ClassificationChoiceDescriptor],
    type[ClassificationType],
    type[Examination],
    type[ExaminationType],
    type[Finding],
    type[FindingType],
    type[Indication],
    type[IndicationType],
    type[Intervention],
    type[InterventionType],
    type[Unit],
    type[UnitType],
    type[InformationSource],
]


class KB_DJANGO_MODEL_BY_NAME_TYPE(TypedDict):
    citation: type[Citation]
    classification: type[Classification]
    classification_type: type[ClassificationType]
    classification_choice: type[ClassificationChoice]
    classification_choice_descriptor: type[ClassificationChoiceDescriptor]
    examination: type[Examination]
    examination_type: type[ExaminationType]
    finding: type[Finding]
    finding_type: type[FindingType]
    indication: type[Indication]
    indication_type: type[IndicationType]
    intervention: type[Intervention]
    intervention_type: type[InterventionType]
    unit: type[Unit]
    unit_type: type[UnitType]
    information_source: type[InformationSource]


KB_DJANGO_MODEL_BY_NAME = KB_DJANGO_MODEL_BY_NAME_TYPE(
    citation=Citation,
    classification=Classification,
    classification_type=ClassificationType,
    classification_choice=ClassificationChoice,
    classification_choice_descriptor=ClassificationChoiceDescriptor,
    examination=Examination,
    examination_type=ExaminationType,
    finding=Finding,
    finding_type=FindingType,
    indication=Indication,
    indication_type=IndicationType,
    intervention=Intervention,
    intervention_type=InterventionType,
    unit=Unit,
    unit_type=UnitType,
    information_source=InformationSource,
)
