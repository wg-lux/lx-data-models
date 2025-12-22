from typing import TypedDict, Union

from lx_dtypes.models.core.citation import CitationDataDict
from lx_dtypes.models.core.classification import (
    ClassificationDataDict,
    ClassificationTypeDataDict,
)
from lx_dtypes.models.core.classification_choice import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.core.examination import (
    ExaminationDataDict,
    ExaminationTypeDataDict,
)
from lx_dtypes.models.core.finding import (
    FindingDataDict,
    FindingTypeDataDict,
)
from lx_dtypes.models.core.indication import (
    IndicationDataDict,
    IndicationTypeDataDict,
)
from lx_dtypes.models.core.intervention import (
    InterventionDataDict,
    InterventionTypeDataDict,
)
from lx_dtypes.models.core.unit import (
    UnitDataDict,
    UnitTypeDataDict,
)

KB_DEEP_DDICT_LIST = [
    CitationDataDict,
    ClassificationDataDict,
    ClassificationTypeDataDict,
    ClassificationChoiceDataDict,
    ClassificationChoiceDescriptorDataDict,
    ExaminationDataDict,
    ExaminationTypeDataDict,
    FindingDataDict,
    FindingTypeDataDict,
    IndicationDataDict,
    IndicationTypeDataDict,
    InterventionDataDict,
    InterventionTypeDataDict,
    UnitDataDict,
    UnitTypeDataDict,
]

KB_DEEP_UNION_DDICT_LIST = Union[
    CitationDataDict,
    ClassificationDataDict,
    ClassificationTypeDataDict,
    ClassificationChoiceDataDict,
    ClassificationChoiceDescriptorDataDict,
    ExaminationDataDict,
    ExaminationTypeDataDict,
    FindingDataDict,
    FindingTypeDataDict,
    IndicationDataDict,
    IndicationTypeDataDict,
    InterventionDataDict,
    InterventionTypeDataDict,
    UnitDataDict,
    UnitTypeDataDict,
]

KB_DEEP_UNION_DDICT_TYPE_LIST = Union[
    type[CitationDataDict],
    type[ClassificationDataDict],
    type[ClassificationTypeDataDict],
    type[ClassificationChoiceDataDict],
    type[ClassificationChoiceDescriptorDataDict],
    type[ExaminationDataDict],
    type[ExaminationTypeDataDict],
    type[FindingDataDict],
    type[FindingTypeDataDict],
    type[IndicationDataDict],
    type[IndicationTypeDataDict],
    type[InterventionDataDict],
    type[InterventionTypeDataDict],
    type[UnitDataDict],
    type[UnitTypeDataDict],
]


class KB_DEEP_DDICT_BY_NAME_TYPE(TypedDict):
    citation: type[CitationDataDict]
    classification: type[ClassificationDataDict]
    classification_type: type[ClassificationTypeDataDict]
    classification_choice: type[ClassificationChoiceDataDict]
    classification_choice_descriptor: type[ClassificationChoiceDescriptorDataDict]
    examination: type[ExaminationDataDict]
    examination_type: type[ExaminationTypeDataDict]
    finding: type[FindingDataDict]
    finding_type: type[FindingTypeDataDict]
    indication: type[IndicationDataDict]
    indication_type: type[IndicationTypeDataDict]
    intervention: type[InterventionDataDict]
    intervention_type: type[InterventionTypeDataDict]
    unit: type[UnitDataDict]
    unit_type: type[UnitTypeDataDict]


KB_DEEP_DDICT_BY_NAME = KB_DEEP_DDICT_BY_NAME_TYPE(
    citation=CitationDataDict,
    classification=ClassificationDataDict,
    classification_type=ClassificationTypeDataDict,
    classification_choice=ClassificationChoiceDataDict,
    classification_choice_descriptor=ClassificationChoiceDescriptorDataDict,
    examination=ExaminationDataDict,
    examination_type=ExaminationTypeDataDict,
    finding=FindingDataDict,
    finding_type=FindingTypeDataDict,
    indication=IndicationDataDict,
    indication_type=IndicationTypeDataDict,
    intervention=InterventionDataDict,
    intervention_type=InterventionTypeDataDict,
    unit=UnitDataDict,
    unit_type=UnitTypeDataDict,
)
