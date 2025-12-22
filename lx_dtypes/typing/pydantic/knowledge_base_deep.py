from typing import TypedDict, Union

from lx_dtypes.models.core.citation import Citation
from lx_dtypes.models.core.classification import (
    Classification,
    ClassificationType,
)
from lx_dtypes.models.core.classification_choice import (
    ClassificationChoice,
)
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.core.examination import (
    Examination,
    ExaminationType,
)
from lx_dtypes.models.core.finding import (
    Finding,
    FindingType,
)
from lx_dtypes.models.core.indication import (
    Indication,
    IndicationType,
)
from lx_dtypes.models.core.intervention import (
    Intervention,
    InterventionType,
)
from lx_dtypes.models.core.unit import (
    Unit,
    UnitType,
)

KB_DEEP_PYDANTIC_LIST = [
    Citation,
    Classification,
    ClassificationType,
    ClassificationChoice,
    ClassificationChoiceDescriptor,
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
]

KB_DEEP_UNION_PYDANTIC_LIST = Union[
    Citation,
    Classification,
    ClassificationType,
    ClassificationChoice,
    ClassificationChoiceDescriptor,
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
]

KB_DEEP_UNION_PYDANTIC_TYPE_LIST = Union[
    type[Citation],
    type[Classification],
    type[ClassificationType],
    type[ClassificationChoice],
    type[ClassificationChoiceDescriptor],
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
]


class KB_DEEP_PYDANTIC_BY_NAME_TYPE(TypedDict):
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


KB_DEEP_PYDANTIC_BY_NAME = KB_DEEP_PYDANTIC_BY_NAME_TYPE(
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
)
