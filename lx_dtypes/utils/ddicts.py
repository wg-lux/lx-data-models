from typing import Dict, Union

from lx_dtypes.models.core.center import CenterDataDict
from lx_dtypes.models.core.citation import CitationDataDict
from lx_dtypes.models.core.classification import (
    ClassificationDataDict,
)
from lx_dtypes.models.core.classification_choice import (
    ClassificationChoiceDataDict,
)
from lx_dtypes.models.core.classification_choice_descriptor import (
    ClassificationChoiceDescriptorDataDict,
)
from lx_dtypes.models.shallow.center import CenterShallowDataDict
from lx_dtypes.models.shallow.citation import CitationShallowDataDict
from lx_dtypes.models.shallow.classification import (
    ClassificationShallowDataDict,
)
from lx_dtypes.models.shallow.classification_choice import (
    ClassificationChoiceShallowDataDict,
)
from lx_dtypes.models.shallow.classification_choice_descriptor import (
    ClassificationChoiceDescriptorShallowDataDict,
)

ddict_types = Union[
    type[CenterDataDict],
    type[CenterShallowDataDict],
    type[CitationDataDict],
    type[CitationShallowDataDict],
    type[ClassificationDataDict],
    type[ClassificationShallowDataDict],
    type[ClassificationChoiceDescriptorDataDict],
    type[ClassificationChoiceDescriptorShallowDataDict],
    type[ClassificationChoiceDataDict],
    type[ClassificationChoiceShallowDataDict],
]

ddicts: Dict[str, ddict_types] = {
    "center": CenterDataDict,
    "center_shallow": CenterShallowDataDict,
    "citation": CitationDataDict,
    "citation_shallow": CitationShallowDataDict,
    "classification": ClassificationDataDict,
    "classification_shallow": ClassificationShallowDataDict,
    "classification_choice_descriptor": ClassificationChoiceDescriptorDataDict,
    "classification_choice_descriptor_shallow": ClassificationChoiceDescriptorShallowDataDict,
    "classification_choice": ClassificationChoiceDataDict,
    "classification_choice_shallow": ClassificationChoiceShallowDataDict,
}
