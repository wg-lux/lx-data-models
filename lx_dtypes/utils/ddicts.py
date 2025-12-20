from typing import Dict, Union

from lx_dtypes.models.base_models.base_model import KnowledgeBaseModelDataDict
from lx_dtypes.models.core.center import CenterDataDict
from lx_dtypes.models.core.center_shallow import CenterShallowDataDict
from lx_dtypes.models.core.citation import CitationDataDict
from lx_dtypes.models.core.citation_shallow import CitationShallowDataDict
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
from lx_dtypes.models.core.examination import (
    ExaminationDataDict,
    ExaminationTypeDataDict,
)
from lx_dtypes.models.core.examination_shallow import (
    ExaminationShallowDataDict,
    ExaminationTypeShallowDataDict,
)
from lx_dtypes.models.core.finding import (
    FindingDataDict,
    FindingTypeDataDict,
)
from lx_dtypes.models.core.finding_shallow import (
    FindingShallowDataDict,
    FindingTypeShallowDataDict,
)
from lx_dtypes.models.core.indication import (
    IndicationDataDict,
    IndicationTypeDataDict,
)
from lx_dtypes.models.core.indication_shallow import (
    IndicationShallowDataDict,
    IndicationTypeShallowDataDict,
)
from lx_dtypes.models.core.intervention import (
    InterventionDataDict,
    InterventionTypeDataDict,
)
from lx_dtypes.models.core.intervention_shallow import (
    InterventionShallowDataDict,
    InterventionTypeShallowDataDict,
)
from lx_dtypes.models.core.unit import (
    UnitDataDict,
    UnitTypeDataDict,
)
from lx_dtypes.models.core.unit_shallow import (
    UnitShallowDataDict,
    UnitTypeShallowDataDict,
)

KB_SHALLOW_DDICT_LIST = [
    KnowledgeBaseModelDataDict,
    CenterShallowDataDict,
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
    CenterShallowDataDict,
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
    type[CenterShallowDataDict],
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

KB_DEEP_DDICT_LIST = [
    CenterDataDict,
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
    CenterDataDict,
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
    type[CenterDataDict],
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

KB_DDICT_LIST = KB_SHALLOW_DDICT_LIST + KB_DEEP_DDICT_LIST

KB_UNION_DDICT_LIST = Union[
    KB_SHALLOW_UNION_DDICT_LIST,
    KB_DEEP_UNION_DDICT_LIST,
]

KB_UNION_DDICT_TYPE_LIST = Union[
    KB_SHALLOW_UNION_DDICT_TYPE_LIST,
    KB_DEEP_UNION_DDICT_TYPE_LIST,
]

UNION_DDICT_TYPE_LIST = KB_UNION_DDICT_TYPE_LIST  # add patient ddicts later


kb_shallow_ddicts: Dict[str, KB_SHALLOW_UNION_DDICT_TYPE_LIST] = {
    "center_shallow": CenterShallowDataDict,
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

kb_deep_ddicts: Dict[str, KB_DEEP_UNION_DDICT_TYPE_LIST] = {
    "center": CenterDataDict,
    "citation": CitationDataDict,
    "classification": ClassificationDataDict,
    "classification_type": ClassificationTypeDataDict,
    "classification_choice": ClassificationChoiceDataDict,
    "classification_choice_descriptor": ClassificationChoiceDescriptorDataDict,
    "examination": ExaminationDataDict,
    "examination_type": ExaminationTypeDataDict,
    "finding": FindingDataDict,
    "finding_type": FindingTypeDataDict,
    "indication": IndicationDataDict,
    "indication_type": IndicationTypeDataDict,
    "intervention": InterventionDataDict,
    "intervention_type": InterventionTypeDataDict,
    "unit": UnitDataDict,
    "unit_type": UnitTypeDataDict,
}

kb_ddicts: Dict[str, KB_UNION_DDICT_TYPE_LIST] = {}
kb_ddicts.update(kb_shallow_ddicts)
kb_ddicts.update(kb_deep_ddicts)

ddicts = kb_ddicts
