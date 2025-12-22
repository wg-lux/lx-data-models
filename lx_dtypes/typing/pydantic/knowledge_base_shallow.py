from typing import TypedDict, Union

from lx_dtypes.models.core.citation_shallow import CitationShallow
from lx_dtypes.models.core.classification_choice_descriptor_shallow import (
    ClassificationChoiceDescriptorShallow,
)
from lx_dtypes.models.core.classification_choice_shallow import (
    ClassificationChoiceShallow,
)
from lx_dtypes.models.core.classification_shallow import (
    ClassificationShallow,
    ClassificationTypeShallow,
)
from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallow,
    ExaminationTypeShallow,
)
from lx_dtypes.models.core.finding_shallow import (
    FindingShallow,
    FindingTypeShallow,
)
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallow,
    IndicationTypeShallow,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallow,
    InterventionTypeShallow,
)
from lx_dtypes.models.core.unit_shallow import (
    UnitShallow,
    UnitTypeShallow,
)

KB_SHALLOW_PYDANTIC_LIST = [
    CitationShallow,
    ClassificationShallow,
    ClassificationTypeShallow,
    ClassificationChoiceShallow,
    ClassificationChoiceDescriptorShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
    InterventionShallow,
    InterventionTypeShallow,
    UnitShallow,
    UnitTypeShallow,
]

KB_SHALLOW_UNION_PYDANTIC_LIST = Union[
    CitationShallow,
    ClassificationShallow,
    ClassificationTypeShallow,
    ClassificationChoiceShallow,
    ClassificationChoiceDescriptorShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
    InterventionShallow,
    InterventionTypeShallow,
    UnitShallow,
    UnitTypeShallow,
]

KB_SHALLOW_UNION_PYDANTIC_TYPE_LIST = Union[
    type[CitationShallow],
    type[ClassificationShallow],
    type[ClassificationTypeShallow],
    type[ClassificationChoiceShallow],
    type[ClassificationChoiceDescriptorShallow],
    type[ExaminationShallow],
    type[ExaminationTypeShallow],
    type[FindingShallow],
    type[FindingTypeShallow],
    type[IndicationShallow],
    type[IndicationTypeShallow],
    type[InterventionShallow],
    type[InterventionTypeShallow],
    type[UnitShallow],
    type[UnitTypeShallow],
]


class KB_SHALLOW_PYDANTIC_BY_NAME_TYPE(TypedDict):
    citation: type[CitationShallow]
    classification: type[ClassificationShallow]
    classification_type: type[ClassificationTypeShallow]
    classification_choice: type[ClassificationChoiceShallow]
    classification_choice_descriptor: type[ClassificationChoiceDescriptorShallow]
    examination: type[ExaminationShallow]
    examination_type: type[ExaminationTypeShallow]
    finding: type[FindingShallow]
    finding_type: type[FindingTypeShallow]
    indication: type[IndicationShallow]
    indication_type: type[IndicationTypeShallow]
    intervention: type[InterventionShallow]
    intervention_type: type[InterventionTypeShallow]
    unit: type[UnitShallow]
    unit_type: type[UnitTypeShallow]


KB_SHALLOW_PYDANTIC_BY_NAME = KB_SHALLOW_PYDANTIC_BY_NAME_TYPE(
    citation=CitationShallow,
    classification=ClassificationShallow,
    classification_type=ClassificationTypeShallow,
    classification_choice=ClassificationChoiceShallow,
    classification_choice_descriptor=ClassificationChoiceDescriptorShallow,
    examination=ExaminationShallow,
    examination_type=ExaminationTypeShallow,
    finding=FindingShallow,
    finding_type=FindingTypeShallow,
    indication=IndicationShallow,
    indication_type=IndicationTypeShallow,
    intervention=InterventionShallow,
    intervention_type=InterventionTypeShallow,
    unit=UnitShallow,
    unit_type=UnitTypeShallow,
)
