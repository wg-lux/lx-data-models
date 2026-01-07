from typing import List

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.BooleanDescriptorMixin import (
    BooleanDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.NumericDescriptorMixin import (
    NumericDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.SelectionDescriptorMixin import (
    SelectionDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.TextDescriptorMixin import (
    TextDescriptorMixin,
)
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.UnitMixin import (
    UnitMixin,
)
from lx_dtypes.names import (
    CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS,
)

from .ClassificationChoiceDescriptorDataDict import (
    ClassificationChoiceDescriptorDataDict,
)


class ClassificationChoiceDescriptor(
    KnowledgebaseBaseModel[ClassificationChoiceDescriptorDataDict],
    NumericDescriptorMixin,
    SelectionDescriptorMixin,
    BooleanDescriptorMixin,
    UnitMixin,
    TextDescriptorMixin,
):
    """
    Model for classification choice descriptors in a knowledge base."""

    name: str

    @classmethod
    def list_type_fields(cls) -> List[str]:
        return CLASSIFICATION_CHOICE_DESCRIPTOR_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[ClassificationChoiceDescriptorDataDict]:
        return ClassificationChoiceDescriptorDataDict
