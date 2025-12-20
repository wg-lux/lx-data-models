from typing import Dict, Union

from lx_dtypes.models.base_models.base_model import KnowledgeBaseModelDataDict
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
    KnowledgeBaseModelDataDict,
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
    KnowledgeBaseModelDataDict,
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
    type[KnowledgeBaseModelDataDict],
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

KB_SHALLOW_DDICT_BY_NAME: Dict[str, KB_SHALLOW_UNION_DDICT_TYPE_LIST] = {
    "citation_shallow": CitationShallowDataDict,
    "classification_shallow": ClassificationShallowDataDict,
    "classification_type_shallow": ClassificationTypeShallowDataDict,
    "classification_choice_shallow": ClassificationChoiceShallowDataDict,
    "classification_choice_descriptor_shallow": ClassificationChoiceDescriptorShallowDataDict,
    "examination_shallow": ExaminationShallowDataDict,
    "examination_type_shallow": ExaminationTypeShallowDataDict,
    "finding_shallow": FindingShallowDataDict,
    "finding_type_shallow": FindingTypeShallowDataDict,
    "indication_shallow": IndicationShallowDataDict,
    "indication_type_shallow": IndicationTypeShallowDataDict,
    "intervention_shallow": InterventionShallowDataDict,
    "intervention_type_shallow": InterventionTypeShallowDataDict,
    "unit_shallow": UnitShallowDataDict,
    "unit_type_shallow": UnitTypeShallowDataDict,
}
