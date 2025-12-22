from typing import TypedDict, Union

from lx_dtypes.models.core.citation_shallow import CitationShallowDataDict
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallowDataDict,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallowDataDict,
)
from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallowDataDict,
    ClassificationTypeShallowDataDict,
)
from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
)
from lx_dtypes.models.core.finding_shallow import (
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
)
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallowDataDict,
    InterventionTypeShallowDataDict,
)
from lx_dtypes.models.core.unit_shallow import (
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
)

KB_SHALLOW_DDICT_LIST = [
    CitationShallowDataDict,
    ClassificationShallowDataDict,
    ClassificationTypeShallowDataDict,
    ClassificationChoiceShallowDataDict,
    ClassificationChoiceDescriptorShallowDataDict,
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
    InterventionShallowDataDict,
    InterventionTypeShallowDataDict,
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
]

KB_SHALLOW_UNION_DDICT_LIST = Union[
    CitationShallowDataDict,
    ClassificationShallowDataDict,
    ClassificationTypeShallowDataDict,
    ClassificationChoiceShallowDataDict,
    ClassificationChoiceDescriptorShallowDataDict,
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
    InterventionShallowDataDict,
    InterventionTypeShallowDataDict,
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
]

KB_SHALLOW_UNION_DDICT_TYPE_LIST = Union[
    type[CitationShallowDataDict],
    type[ClassificationShallowDataDict],
    type[ClassificationTypeShallowDataDict],
    type[ClassificationChoiceShallowDataDict],
    type[ClassificationChoiceDescriptorShallowDataDict],
    type[ExaminationShallowDataDict],
    type[ExaminationTypeShallowDataDict],
    type[FindingShallowDataDict],
    type[FindingTypeShallowDataDict],
    type[IndicationShallowDataDict],
    type[IndicationTypeShallowDataDict],
    type[InterventionShallowDataDict],
    type[InterventionTypeShallowDataDict],
    type[UnitShallowDataDict],
    type[UnitTypeShallowDataDict],
]


class KB_SHALLOW_DDICT_BY_NAME_TYPE(TypedDict):
    citation: type[CitationShallowDataDict]
    classification: type[ClassificationShallowDataDict]
    classification_type: type[ClassificationTypeShallowDataDict]
    classification_choice: type[ClassificationChoiceShallowDataDict]
    classification_choice_descriptor: type[
        ClassificationChoiceDescriptorShallowDataDict
    ]
    examination: type[ExaminationShallowDataDict]
    examination_type: type[ExaminationTypeShallowDataDict]
    finding: type[FindingShallowDataDict]
    finding_type: type[FindingTypeShallowDataDict]
    indication: type[IndicationShallowDataDict]
    indication_type: type[IndicationTypeShallowDataDict]
    intervention: type[InterventionShallowDataDict]
    intervention_type: type[InterventionTypeShallowDataDict]
    unit: type[UnitShallowDataDict]
    unit_type: type[UnitTypeShallowDataDict]


KB_SHALLOW_DDICT_BY_NAME = KB_SHALLOW_DDICT_BY_NAME_TYPE(
    citation=CitationShallowDataDict,
    classification=ClassificationShallowDataDict,
    classification_type=ClassificationTypeShallowDataDict,
    classification_choice=ClassificationChoiceShallowDataDict,
    classification_choice_descriptor=ClassificationChoiceDescriptorShallowDataDict,
    examination=ExaminationShallowDataDict,
    examination_type=ExaminationTypeShallowDataDict,
    finding=FindingShallowDataDict,
    finding_type=FindingTypeShallowDataDict,
    indication=IndicationShallowDataDict,
    indication_type=IndicationTypeShallowDataDict,
    intervention=InterventionShallowDataDict,
    intervention_type=InterventionTypeShallowDataDict,
    unit=UnitShallowDataDict,
    unit_type=UnitTypeShallowDataDict,
)
